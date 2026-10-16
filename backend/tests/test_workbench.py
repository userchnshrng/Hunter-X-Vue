from datetime import datetime, timezone
from pathlib import Path

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from fastapi.testclient import TestClient
from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.core.auth import digest
from app.main import create_app
from app.models import AuthSession, Base


def post(client, path, body):
    response = client.post(f"/api/v1{path}", json=body)
    assert response.status_code in (200, 201), response.text
    return response.json()


def records(client):
    company = post(client, "/companies", {"name": "合成示例科技", "industry": "软件"})
    candidate = post(
        client,
        "/candidates",
        {"name": "合成人才", "current_company_name": "原公司", "current_title": "产品负责人"},
    )
    job = post(client, "/jobs", {"company_id": company["id"], "title": "产品总监", "team_size": 0})
    return company, candidate, job


def test_initial_migration_matches_models(context):
    _, app, _ = context
    with app.state.engine.connect() as connection:
        assert len(inspect(connection).get_table_names()) == 11
        assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []


def test_auth_rotation_logout_and_private_api(context):
    client, app, password = context
    assert client.get("/api/v1/candidates").status_code == 401
    assert (
        client.post(
            "/api/v1/auth/login", json={"username": "synthetic-admin", "password": password}
        ).status_code
        == 403
    )
    assert client.post("/api/v1/auth/refresh").status_code == 403
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "synthetic-admin", "password": password},
        headers={"X-Hunter-Client": "web"},
    )
    assert login.status_code == 200
    assert "HttpOnly" in login.headers["set-cookie"]
    assert "SameSite=strict" in login.headers["set-cookie"]
    old_access = login.json()["access_token"]
    old_refresh = client.cookies.get("hunter_refresh")
    rotated = client.post("/api/v1/auth/refresh", headers={"X-Hunter-Client": "web"})
    assert rotated.status_code == 200
    client.headers["Authorization"] = f"Bearer {old_access}"
    assert client.get("/api/v1/candidates").status_code == 401
    access = rotated.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {access}"
    assert client.get("/api/v1/candidates").status_code == 200
    with Session(app.state.engine) as db:
        session = db.scalar(select(AuthSession).where(AuthSession.access_hash == digest(access)))
        assert session.refresh_hash != digest(old_refresh)
        assert access != session.access_hash
    assert client.post("/api/v1/auth/logout", headers={"X-Hunter-Client": "web"}).status_code == 200
    assert client.get("/api/v1/candidates").status_code == 401
    assert client.post("/api/v1/auth/refresh", headers={"X-Hunter-Client": "web"}).status_code == 401


def test_login_errors_do_not_echo_password(context):
    client, _, _ = context
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "missing", "password": "synthetic-only"},
        headers={"X-Hunter-Client": "web"},
    )
    assert response.status_code == 401
    assert "synthetic-only" not in response.text
    assert response.json()["request_id"]


def test_candidates_jobs_communication_and_independent_applications(client):
    company, candidate, job = records(client)
    other = post(client, "/jobs", {"company_id": company["id"], "title": "业务负责人", "team_size": None})
    first = post(client, "/applications", {"candidate_id": candidate["id"], "job_id": job["id"]})
    repeated = post(client, "/applications", {"candidate_id": candidate["id"], "job_id": job["id"]})
    second = post(client, "/applications", {"candidate_id": candidate["id"], "job_id": other["id"]})
    assert first["id"] == repeated["id"]
    assert (
        client.patch(f"/api/v1/applications/{first['id']}", json={"status": "interview"}).status_code == 200
    )
    post(
        client,
        f"/candidates/{candidate['id']}/employments",
        {"company_name": "原公司", "title": "产品负责人", "start_month": "2020-05", "is_current": True},
    )
    post(
        client,
        f"/candidates/{candidate['id']}/communications",
        {
            "content": "第一次合成沟通",
            "application_id": first["id"],
            "occurred_at": "2026-10-16T10:00:00+08:00",
        },
    )
    post(client, f"/candidates/{candidate['id']}/communications", {"content": "补录历史，时间未知"})
    detail = client.get(f"/api/v1/candidates/{candidate['id']}").json()
    by_id = {item["id"]: item for item in detail["applications"]}
    assert by_id[first["id"]]["status"] == "interview"
    assert by_id[second["id"]]["status"] == "pending"
    assert len(detail["employments"]) == 1
    assert len(detail["communications"]) == 2
    assert detail["communications"][0]["content"] == "第一次合成沟通"
    assert detail["contacted_on"] is None
    assert client.get(f"/api/v1/jobs/{job['id']}").json()["team_size"] == 0
    assert client.get(f"/api/v1/jobs/{other['id']}").json()["team_size"] is None


def test_relation_validation_and_negative_team_size(client):
    company, candidate, job = records(client)
    other = post(client, "/candidates", {"name": "另一个合成人才"})
    application = post(client, "/applications", {"candidate_id": candidate["id"], "job_id": job["id"]})
    assert (
        client.post(
            f"/api/v1/candidates/{other['id']}/communications",
            json={"content": "不能挂到别人的推荐", "application_id": application["id"]},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/jobs", json={"company_id": company["id"], "title": "测试", "team_size": -1}
        ).status_code
        == 422
    )
    assert client.post("/api/v1/jobs", json={"company_id": "missing", "title": "测试"}).status_code == 404
    assert client.post("/api/v1/candidates", json={"name": "  "}).status_code == 422
    assert (
        client.patch(f"/api/v1/applications/{application['id']}", json={"status": "invented"}).status_code
        == 422
    )
    assert client.get("/api/v1/candidates?page_size=1000").status_code == 422


def test_search_same_name_and_company_facts(client):
    company, _, _ = records(client)
    post(client, "/candidates", {"name": "合成人才", "current_company_name": "另一家公司"})
    assert client.get("/api/v1/candidates", params={"q": "合成人才"}).json()["total"] == 2
    assert client.get("/api/v1/candidates", params={"q": "原公司"}).json()["total"] == 1
    post(
        client,
        f"/companies/{company['id']}/facts",
        {"content": "合成业务公告", "source": "用户提供的测试公告", "fact_date": "2026-09-01"},
    )
    fact = client.get(f"/api/v1/companies/{company['id']}").json()["facts"][0]
    assert fact["fact_date"] == "2026-09-01"
    recorded_at = datetime.fromisoformat(fact["created_at"]).replace(tzinfo=timezone.utc)
    assert abs((datetime.now(timezone.utc) - recorded_at).total_seconds()) < 60
    assert (
        client.post(
            f"/api/v1/companies/{company['id']}/facts",
            json={"content": "测试", "source": "来源", "source_url": "javascript:alert(1)"},
        ).status_code
        == 422
    )


def test_private_file_upload_magic_and_download(client, context):
    _, candidate, _ = records(client)
    data = "合成简历：产品负责人".encode()
    response = client.post(f"/api/v1/files/candidate/{candidate['id']}", files={"file": ("resume.txt", data)})
    assert response.status_code == 201, response.text
    asset = response.json()
    assert asset["parse_status"] == "not_started"
    url = f"/api/v1/files/{asset['id']}/download"
    assert client.get(url).content == data
    assert len(client.get(f"/api/v1/files/owners/candidate/{candidate['id']}").json()) == 1
    _, app, _ = context
    with TestClient(create_app(app.state.settings)) as anonymous:
        assert anonymous.get(url).status_code == 401
    assert (
        client.post(
            f"/api/v1/files/candidate/{candidate['id']}", files={"file": ("fake.pdf", b"not a pdf")}
        ).status_code
        == 422
    )
    assert not (app.state.settings.upload_root / "resume.txt").exists()
    assert all(Path(p).name != "resume.txt" for p in app.state.settings.upload_root.iterdir())


def test_data_survives_application_restart(client, context):
    _, candidate, _ = records(client)
    _, app, _ = context
    token = client.headers["Authorization"]
    with TestClient(create_app(app.state.settings)) as restarted:
        response = restarted.get(f"/api/v1/candidates/{candidate['id']}", headers={"Authorization": token})
        assert response.status_code == 200
        assert response.json()["name"] == "合成人才"
