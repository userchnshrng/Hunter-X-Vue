import argparse
from getpass import getpass

from alembic import command
from alembic.config import Config
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import passwords
from app.core.config import PROJECT_ROOT, settings
from app.core.database import make_engine
from app.models import User


def main():
    parser = argparse.ArgumentParser(description="猎头工作台本地管理命令")
    parser.add_argument("command", choices=["init-db", "create-admin"])
    parser.add_argument("--username", default="admin")
    args = parser.parse_args()
    if args.command == "init-db":
        (PROJECT_ROOT / "var").mkdir(parents=True, exist_ok=True)
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
