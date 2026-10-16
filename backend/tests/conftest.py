import secrets
import tempfile
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.auth import passwords
from app.core.config import PROJECT_ROOT, Settings
from app.main import create_app
from app.models import User


class TestContext(tuple):
    __test__ = False

    def __repr__(self):
        return "<isolated application context; credentials redacted>"


@pytest.fixture
def context():
    # Leave isolated artifacts in the system temp directory; do not delete user files.
    root = Path(tempfile.mkdtemp(prefix="hunter-stage-a-test-"))
    url = f"sqlite:///{(root / 'test.db').as_posix()}"
    config = Config(str(PROJECT_ROOT / "backend" / "alembic.ini"))
    config.attributes["database_url"] = url
    command.upgrade(config, "head")
    app = create_app(Settings(database_url=url, upload_root=root / "uploads"))
    password = secrets.token_urlsafe(24)
    with Session(app.state.engine) as db:
        db.add(
            User(
                username="synthetic-admin",
                display_name="合成测试账号",
                password_hash=passwords.hash(password),
            )
        )
        db.commit()
    with TestClient(app) as client:
        yield TestContext((client, app, password))


@pytest.fixture
def client(context):
    client, _, password = context
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "synthetic-admin", "password": password},
        headers={"X-Hunter-Client": "web"},
    )
    assert response.status_code == 200
    client.headers["Authorization"] = f"Bearer {response.json()['access_token']}"
    return client
