import hashlib
import secrets
from datetime import timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import AuthSession, User, now

passwords = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)
DUMMY_HASH = passwords.hash(secrets.token_urlsafe(32))
Db = Annotated[Session, Depends(get_db)]


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def aware(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def require_client(request: Request):
    if request.headers.get("X-Hunter-Client") != "web":
        raise HTTPException(403, "请求来源验证失败，请从工作台重试")


def create_session(db: Session, user: User, config):
    access, refresh = secrets.token_urlsafe(32), secrets.token_urlsafe(48)
    session = AuthSession(
        user_id=user.id,
        access_hash=digest(access),
        refresh_hash=digest(refresh),
        access_expires_at=now() + timedelta(minutes=config.access_minutes),
        refresh_expires_at=now() + timedelta(days=config.refresh_days),
    )
    db.add(session)
    db.flush()
    return session, access, refresh


def current_user(db: Db, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    if not credentials:
        raise HTTPException(401, "请先登录")
    session = db.scalar(select(AuthSession).where(AuthSession.access_hash == digest(credentials.credentials)))
    if not session or session.revoked_at or aware(session.access_expires_at) <= now():
        raise HTTPException(401, "登录已过期，请重新登录")
    user = db.get(User, session.user_id)
    if not user or not user.active:
        raise HTTPException(401, "账号不可用")
    return user


CurrentUser = Annotated[User, Depends(current_user)]
