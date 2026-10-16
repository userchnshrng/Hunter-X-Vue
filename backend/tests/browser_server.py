"""Disposable browser-test database. Credentials are supplied only in the child process environment."""

import os
import tempfile
from pathlib import Path

import uvicorn
from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session

from app.core.auth import passwords
from app.core.config import PROJECT_ROOT, Settings
from app.main import create_app
from app.models import User


def main():
    password = os.environ["HUNTER_TEST_PASSWORD"]
    root = Path(tempfile.mkdtemp(prefix="hunter-browser-test-"))
    url = f"sqlite:///{(root / 'test.db').as_posix()}"
    config = Config(str(PROJECT_ROOT / "backend" / "alembic.ini"))
    config.attributes["database_url"] = url
    command.upgrade(config, "head")
    app = create_app(Settings(database_url=url, upload_root=root / "uploads"))
    with Session(app.state.engine) as db:
        db.add(
            User(username="browser-test", display_name="合成测试账号", password_hash=passwords.hash(password))
        )
        db.commit()
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=int(os.environ.get("HUNTER_TEST_PORT", "8001")),
        access_log=False,
        log_level="warning",
    )


if __name__ == "__main__":
    main()
