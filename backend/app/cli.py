import argparse
import sqlite3
from datetime import datetime, timezone
from getpass import getpass
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.auth import passwords
from app.core.config import PROJECT_ROOT, settings
from app.core.database import make_engine
from app.models import User


def upgrade_local_database():
    database = make_url(settings.database_url)
    target = (PROJECT_ROOT / "var/hunter.db").resolve()
    if (
        database.get_backend_name() != "sqlite"
        or not database.database
        or Path(database.database).resolve() != target
    ):
        raise RuntimeError("此升级入口仅用于已授权的 var/hunter.db SQLite 开发库")
    with sqlite3.connect(f"file:{target.as_posix()}?mode=ro", uri=True) as source:
        version = source.execute("SELECT version_num FROM alembic_version").fetchone()[0]
        if version == "0002_stage_b":
            print("开发库已在阶段 B 版本，无需重复升级。")
            return
        if version != "0001":
            raise RuntimeError("开发库版本与已授权的 0001→0002 范围不一致")
        root = PROJECT_ROOT / "var/backups"
        root.mkdir(parents=True, exist_ok=True)
        backup = root / f"stage-b-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}.db"
        with backup.open("xb"):
            pass
        with sqlite3.connect(backup) as destination:
            source.backup(destination)
            if destination.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("备份完整性检查失败，未开始升级")
            if destination.execute("SELECT version_num FROM alembic_version").fetchone()[0] != version:
                raise RuntimeError("备份版本检查失败，未开始升级")
    config = Config(str(PROJECT_ROOT / "backend/alembic.ini"))
    config.attributes["database_url"] = settings.database_url
    command.upgrade(config, "0002_stage_b")
    print(f"备份已校验：{backup}")
    print("开发库升级至阶段 B，既有业务记录保留。")


def main():
    parser = argparse.ArgumentParser(description="猎头工作台本地管理命令")
    parser.add_argument("command", choices=["init-db", "upgrade-db", "create-admin"])
    parser.add_argument("--username", default="admin")
    args = parser.parse_args()
    if args.command == "upgrade-db":
        upgrade_local_database()
    elif args.command == "init-db":
        (PROJECT_ROOT / "var").mkdir(parents=True, exist_ok=True)
        target = (PROJECT_ROOT / "var/hunter.db").resolve()
        if target.exists() and make_url(settings.database_url).database == target.as_posix():
            upgrade_local_database()
            return
        config = Config(str(PROJECT_ROOT / "backend" / "alembic.ini"))
        command.upgrade(config, "head")
        print("数据库迁移完成。未创建演示账号。")
    else:
        if not 1 <= len(args.username.strip()) <= 80:
            parser.error("用户名长度应为 1–80")
        password = getpass("设置管理员密码（至少 12 位，不显示）：")
        confirmation = getpass("再次输入：")
        if password != confirmation or len(password) < 12:
            parser.error("密码不一致或不足 12 位")
        with Session(make_engine(settings.database_url)) as db:
            if db.scalar(select(User).where(User.username == args.username.strip())):
                parser.error("用户名已存在；不会覆盖已有账号")
            db.add(
                User(
                    username=args.username.strip(),
                    display_name=args.username.strip(),
                    password_hash=passwords.hash(password),
                    role="admin",
                )
            )
            db.commit()
        print("管理员已创建。请在工作台登录。")


if __name__ == "__main__":
    main()
