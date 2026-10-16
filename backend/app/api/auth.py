from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select, update

from app.core.auth import (
    DUMMY_HASH,
    CurrentUser,
    Db,
    aware,
    create_session,
    digest,
    passwords,
    require_client,
)
from app.models import AuthSession, User, now
from app.schemas import Login

router = APIRouter(prefix="/auth", tags=["auth"])
COOKIE = "hunter_refresh"
COOKIE_PATH = "/api/v1/auth"


def user_data(user):
    return {"id": user.id, "username": user.username, "display_name": user.display_name, "role": user.role}


def auth_result(response, session, access, refresh, user, config):
    response.set_cookie(
        COOKIE,
        refresh,
        httponly=True,
        secure=config.secure_cookies,
        samesite="strict",
        path=COOKIE_PATH,
        max_age=config.refresh_days * 86400,
    )
    response.headers["Cache-Control"] = "no-store"
    return {"access_token": access, "expires_at": session.access_expires_at, "user": user_data(user)}


@router.post("/login", dependencies=[Depends(require_client)])
def login(body: Login, request: Request, response: Response, db: Db):
    user = db.scalar(select(User).where(User.username == body.username))
    # A missing username still performs the same password hashing work.
    verified = passwords.verify(body.password, user.password_hash if user else DUMMY_HASH)
    if not user or not verified or not user.active:
        raise HTTPException(401, "用户名或密码不正确")
    config = request.app.state.settings
    session, access, refresh = create_session(db, user, config)
    db.commit()
    return auth_result(response, session, access, refresh, user, config)


@router.post("/refresh", dependencies=[Depends(require_client)])
def refresh(request: Request, response: Response, db: Db):
    token = request.cookies.get(COOKIE)
    old_hash = digest(token) if token else ""
    session = db.scalar(select(AuthSession).where(AuthSession.refresh_hash == old_hash))
    if not session or session.revoked_at or aware(session.refresh_expires_at) <= now():
        raise HTTPException(401, "登录已失效，请重新登录")
    user = db.get(User, session.user_id)
    if not user or not user.active:
        raise HTTPException(401, "账号不可用")
    import secrets

    access, refresh_token = secrets.token_urlsafe(32), secrets.token_urlsafe(48)
    expires = now() + timedelta(minutes=request.app.state.settings.access_minutes)
    result = db.execute(
        update(AuthSession)
        .where(
            AuthSession.id == session.id,
            AuthSession.refresh_hash == old_hash,
            AuthSession.revoked_at.is_(None),
        )
        .values(access_hash=digest(access), refresh_hash=digest(refresh_token), access_expires_at=expires)
    )
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(401, "登录状态已变化，请重试")
    db.commit()
    db.refresh(session)
    return auth_result(response, session, access, refresh_token, user, request.app.state.settings)


@router.get("/me")
def me(user: CurrentUser):
    return user_data(user)


@router.post("/logout", dependencies=[Depends(require_client)])
def logout(request: Request, response: Response, db: Db):
    token = request.cookies.get(COOKIE)
    session = db.scalar(select(AuthSession).where(AuthSession.refresh_hash == digest(token or "")))
    if session:
        session.revoked_at = now()
        db.commit()
    response.delete_cookie(COOKIE, path=COOKIE_PATH)
    return {"success": True}
