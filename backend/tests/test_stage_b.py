import csv
import io
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from openpyxl import Workbook
from sqlalchemy import event, inspect, select, text
from sqlalchemy.orm import Session

from app.core.auth import passwords
from app.core.config import PROJECT_ROOT
from app.core.database import make_engine
from app.main import create_app
from app.models import Candidate, Communication, User
from tests.test_workbench import post, records


def upload(client, rows, xlsx=False):
    if xlsx:
        workbook = Workbook()
        for row in rows:
            workbook.active.append(row)
        output = io.BytesIO()
        workbook.save(output)
        data, name = output.getvalue(), "synthetic.xlsx"
    else:
        output = io.StringIO()
        csv.writer(output).writerows(rows)
        data, name = output.getvalue().encode("utf-8-sig"), "synthetic.csv"
    response = client.post("/api/v1/imports/upload", files={"file": (name, data)})
    assert response.status_code == 201, response.text
    return response.json()


def preview(client, batch, mapping, header=1):
    return post(
        client,
        f"/imports/{batch['id']}/preview",
        {
            "revision": batch["revision"],
            "sheet_name": batch["sheets"][0]["name"],
            "header_row": header,
            "mapping": mapping,
        },
    )


def rows_of(client, batch):
    return client.get(f"/api/v1/imports/{batch['id']}/rows").json()["items"]


def commit(client, batch, key="synthetic_commit_key_123456"):
    return client.post(
        f"/api/v1/imports/{batch['id']}/commit",
        json={
            "revision": batch["revision"],
            "idempotency_key": key,
        },
    )


def field(client, kind, **kwargs):
    return post(
        client,
        "/custom-fields",
        {"entity_type": "candidate", "label": f"合成{kind}", "value_type": kind, **kwargs},
    )


def test_incremental_upgrade_preserves_previous_data():
    root = Path(tempfile.mkdtemp(prefix="hunter-stage-b-upgrade-"))
    url = f"sqlite:///{(root / 'upgrade.db').as_posix()}"
    config = Config(str(PROJECT_ROOT / "backend/alembic.ini"))
    config.attributes["database_url"] = url
    command.upgrade(config, "0001")
    engine = make_engine(url)
    with Session(engine) as db:
        db.add(Candidate(name="旧记录", custom_fields={"legacy": "旧值"}))
        db.commit()
    command.upgrade(config, "head")
    with Session(engine) as db:
        item = db.scalar(select(Candidate))
        assert item.name == "旧记录" and item.custom_fields == {"legacy": "旧值"}
        assert len(inspect(engine).get_table_names()) == 14
        assert db.scalar(text("SELECT version_num FROM alembic_version")) == "0002_stage_b"
    engine.dispose()


def test_custom_types_required_disable_and_immutable_options(client):
    fields = [
        field(client, "text", required=True),
        field(client, "number"),
        field(client, "date"),
        field(client, "select", options=[{"value": "a", "label": "可沟通"}]),
    ]
    assert client.post("/api/v1/candidates", json={"name": "缺字段"}).status_code == 422
    values = {
        fields[0]["key"]: "杭州",
        fields[1]["key"]: 0,
        fields[2]["key"]: "2026-10-16",
        fields[3]["key"]: "a",
    }
    candidate = post(client, "/candidates", {"name": "合成字段测试", "custom_fields": values})
    for key, value in [
        (fields[1]["key"], True),
        (fields[2]["key"], "2026-02-30"),
        (fields[3]["key"], "invented"),
        ("unknown", "x"),
    ]:
        assert (
            client.patch(
                f"/api/v1/candidates/{candidate['id']}",
                json={
                    "name": "合成字段测试",
                    "custom_fields": {**values, key: value},
                },
            ).status_code
            == 422
        )
    disabled = post_field_update(client, fields[0], enabled=False)
    assert disabled["version"] == 2
    updated = client.patch(f"/api/v1/candidates/{candidate['id']}", json={"name": "保留旧值"})
    assert updated.status_code == 200 and updated.json()["custom_fields"] == values
    assert (
        client.patch(
            f"/api/v1/candidates/{candidate['id']}",
            json={
                "name": "不能改停用值",
                "custom_fields": {fields[0]["key"]: "上海"},
            },
        ).status_code
        == 422
    )
    assert (
        client.patch(
            f"/api/v1/custom-fields/{fields[3]['id']}",
            json={
                **field_body(fields[3]),
                "value_type": "text",
                "options": [],
            },
        ).status_code
        == 422
    )
    assert (
        client.patch(
            f"/api/v1/custom-fields/{fields[3]['id']}",
            json={
                **field_body(fields[3]),
                "options": [{"value": "b", "label": "改值"}],
            },
        ).status_code
        == 422
    )


def field_body(record):
    return {
        key: record[key]
        for key in (
            "entity_type",
            "label",
            "value_type",
            "options",
            "description",
            "required",
            "enabled",
            "position",
            "version",
        )
    }


def post_field_update(client, record, **changes):
    response = client.patch(f"/api/v1/custom-fields/{record['id']}", json={**field_body(record), **changes})
    assert response.status_code == 200, response.text
    return response.json()


def test_xlsx_seven_fields_custom_dates_contacts_and_commit_retry(client, context):
    number = field(client, "number")
    batch = upload(
        client,
        [
            ["日期", "姓名", "公司", "职位", "电话", "微信", "沟通", "来源", "年薪"],
            [
                date(2026, 10, 1),
                "合成林一",
                "未建档公司",
                "产品经理",
                "0012345",
                "wx-synthetic",
                "未知日期的历史沟通",
                "历史库",
                50,
            ],
        ],
        True,
    )
    batch = preview(
        client,
        batch,
        {
            "0": "contacted_on",
            "1": "name",
            "2": "current_company_name",
            "3": "current_title",
            "4": "contact:phone",
            "5": "contact:wechat",
            "6": "communication",
            "7": "resume_source",
            "8": f"custom:{number['key']}",
        },
    )
    assert batch["status"] == "ready"
    result = commit(client, batch)
    assert result.status_code == 200, result.text
    assert commit(client, batch).json() == result.json()
    _, app, _ = context
    with TestClient(create_app(app.state.settings), headers=dict(client.headers)) as restarted:
        assert commit(restarted, batch).json() == result.json()
    candidate = client.get(f"/api/v1/candidates/{result.json()['candidate_ids'][0]}").json()
    assert candidate["current_company_id"] is None
    assert candidate["contacted_on"] == "2026-10-01"
    assert candidate["contact_methods"][0]["value"] == "0012345"
    assert candidate["custom_fields"][number["key"]] == 50
    assert candidate["communications"][0]["occurred_at"] is None
    assert client.get("/api/v1/candidates").json()["total"] == 1


def test_invalid_rows_correction_formula_report_and_no_partial_writes(client):
    batch = upload(
        client, [["姓名", "日期"], ["合成有效", "2026/10/1"], ["=1+2", "03/04/2026"], ["", "2026-10-01"]]
    )
    batch = preview(client, batch, {"0": "name", "1": "contacted_on"})
    assert batch["counts"]["errors"] == 2
    report = client.get(f"/api/v1/imports/{batch['id']}/errors").content.decode("utf-8-sig")
    assert "'=1+2" in report
    assert commit(client, batch).status_code == 409
    assert client.get("/api/v1/candidates").json()["total"] == 0
    batch = client.get(f"/api/v1/imports/{batch['id']}").json()
    for row in rows_of(client, batch):
        if row["errors"]:
            batch = post_patch_row(
                client, batch, row, corrections={"0": f"修正{row['row_number']}", "1": "2026-10-02"}
            )
    assert commit(client, batch).json()["created"] == 3


def post_patch_row(client, batch, row, **values):
    response = client.patch(
        f"/api/v1/imports/{batch['id']}/rows/{row['id']}", json={"revision": batch["revision"], **values}
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_duplicates_require_explicit_decisions_and_new_conflicts_invalidate(client):
    post(client, "/candidates", {"name": "同名", "contact_methods": [{"type": "phone", "value": "001"}]})
    batch = upload(client, [["姓名", "电话"], ["同名", "002"], ["第二人", "001"], ["第三人", "003"]])
    batch = preview(client, batch, {"0": "name", "1": "contact:phone"})
    assert batch["counts"]["review"] == 2
    for row in rows_of(client, batch):
        if row["duplicates"]:
            batch = post_patch_row(
                client, batch, row, decision="skip" if row["row_number"] == 2 else "create"
            )
    post(client, "/candidates", {"name": "并发新增", "contact_methods": [{"type": "phone", "value": "003"}]})
    assert commit(client, batch).status_code == 409
    batch = client.get(f"/api/v1/imports/{batch['id']}").json()
    row = rows_of(client, batch)[2]
    assert row["decision"] == "" and row["duplicates"]
    batch = post_patch_row(client, batch, row, decision="create")
    assert commit(client, batch).json()["created"] == 2
    assert client.get("/api/v1/candidates").json()["total"] == 4


def test_concurrent_commit_and_reused_key(client, context):
    batch = preview(client, upload(client, [["姓名"], ["并发合成"]]), {"0": "name"})
    _, app, _ = context

    def submit(_):
        with TestClient(app, headers=dict(client.headers)) as caller:
            response = commit(caller, batch)
            assert response.status_code == 200, response.text
            return response.json()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(submit, range(2)))
    assert results[0] == results[1]
    assert client.get("/api/v1/candidates").json()["total"] == 1
    another = preview(client, upload(client, [["姓名"], ["另一批次"]]), {"0": "name"})
    assert commit(client, another).status_code == 409
    assert commit(client, {**batch, "revision": batch["revision"] + 1}).status_code == 409


def test_mid_commit_failure_rolls_back_every_record(client, context):
    batch = preview(
        client,
        upload(client, [["姓名", "沟通"], ["合成一", "正常"], ["合成二", "触发失败"]]),
        {"0": "name", "1": "communication"},
    )

    def fail_insert(mapper, connection, record):
        if record.content == "触发失败":
            raise RuntimeError("synthetic transactional failure")

    event.listen(Communication, "before_insert", fail_insert)
    try:
        with pytest.raises(RuntimeError, match="synthetic transactional failure"):
            commit(client, batch)
    finally:
        event.remove(Communication, "before_insert", fail_insert)
    assert client.get("/api/v1/candidates").json()["total"] == 0
    assert all(row["candidate_id"] is None for row in rows_of(client, batch))
    assert commit(client, batch).json()["created"] == 2


def test_changed_fields_stale_row_versions_and_cancel(client):
    definition = field(client, "text")
    batch = preview(client, upload(client, [["姓名"], ["合成"]]), {"0": "name"})
    row = rows_of(client, batch)[0]
    post_field_update(client, definition, label="修改显示名")
    assert commit(client, batch).status_code == 409
    batch = preview(client, batch, {"0": "name"})
    stale = client.patch(
        f"/api/v1/imports/{batch['id']}/rows/{row['id']}", json={"revision": 1, "acknowledged": True}
    )
    assert stale.status_code == 409
    assert client.post(f"/api/v1/imports/{batch['id']}/cancel").json()["status"] == "cancelled"
    assert commit(client, batch).status_code == 409
    assert client.get(f"/api/v1/imports/{batch['id']}/file").status_code == 200


def test_batch_is_private_and_definitions_require_admin(client, context):
    definition = field(client, "text")
    batch = upload(client, [["姓名"], ["合成"]])
    _, app, password = context
    with Session(app.state.engine) as db:
        db.add(
            User(
                username="synthetic-member",
                display_name="合成普通用户",
                role="member",
                password_hash=passwords.hash(password),
            )
        )
        db.commit()
    with TestClient(app) as other:
        auth = other.post(
            "/api/v1/auth/login",
            json={"username": "synthetic-member", "password": password},
            headers={"X-Hunter-Client": "web"},
        )
        other.headers["Authorization"] = f"Bearer {auth.json()['access_token']}"
        assert other.get("/api/v1/imports").json()["total"] == 0
        for suffix in ["", "/rows", "/file", "/errors"]:
            assert other.get(f"/api/v1/imports/{batch['id']}{suffix}").status_code == 404
        assert other.post(f"/api/v1/imports/{batch['id']}/cancel").status_code == 404
        assert other.get("/api/v1/custom-fields?entity_type=candidate").status_code == 200
        assert (
            other.patch(f"/api/v1/custom-fields/{definition['id']}", json=field_body(definition)).status_code
            == 403
        )
        assert (
            other.post(
                "/api/v1/custom-fields", json={"entity_type": "job", "label": "不允许", "value_type": "text"}
            ).status_code
            == 403
        )
    with TestClient(app) as anonymous:
        assert anonymous.get("/api/v1/imports/template").status_code == 401


def test_numeric_contacts_need_review_and_bad_workbooks_are_rejected(client):
    batch = preview(
        client,
        upload(client, [["姓名", "电话"], ["合成数字", 12345]], True),
        {"0": "name", "1": "contact:phone"},
    )
    assert batch["counts"]["review"] == 1
    row = rows_of(client, batch)[0]
    batch = post_patch_row(client, batch, row, acknowledged=True)
    assert commit(client, batch).json()["created"] == 1
    for name, content in [
        ("old.xls", b"old"),
        ("fake.xlsx", b"fake"),
        ("bad.csv", b"\xff\xfe"),
        ("empty.csv", b""),
    ]:
        assert client.post("/api/v1/imports/upload", files={"file": (name, content)}).status_code in (
            413,
            422,
        )
    with pytest.raises(Exception, match="100 列"):
        from app.services.imports import decode_file

        decode_file(("a," * 101).encode(), "csv")


def test_filters_and_child_edit_ownership(client):
    company, candidate, job = records(client)
    changed = {"name": candidate["name"], "resume_source": "合成来源", "contacted_on": "2026-10-01"}
    assert client.patch(f"/api/v1/candidates/{candidate['id']}", json=changed).status_code == 200
    assert (
        client.get(
            "/api/v1/candidates?source=合成来源&contacted_from=2026-10-01&contacted_to=2026-10-01"
        ).json()["total"]
        == 1
    )
    assert (
        client.get("/api/v1/candidates?contacted_from=2026-10-02&contacted_to=2026-10-01").status_code == 422
    )
    assert client.get("/api/v1/candidate-sources").json() == ["合成来源"]
    assert (
        client.get("/api/v1/jobs", params={"q": company["name"], "company_id": company["id"]}).json()["total"]
        == 1
    )
    for path, body, updated in [
        (
            f"/candidates/{candidate['id']}/employments",
            {"company_name": "合成公司", "title": "旧职位"},
            {"company_name": "合成公司", "title": "新职位"},
        ),
        (f"/candidates/{candidate['id']}/communications", {"content": "旧沟通"}, {"content": "新沟通"}),
        (
            f"/companies/{company['id']}/facts",
            {"content": "旧资料", "source": "测试"},
            {"content": "新资料", "source": "测试"},
        ),
    ]:
        item = post(client, path, body)
        response = client.patch(f"/api/v1{path}/{item['id']}", json=updated)
        assert response.status_code == 200 and response.json()["created_at"] == item["created_at"]
        bad_path = path.replace(candidate["id"], "other").replace(company["id"], "other")
        assert client.patch(f"/api/v1{bad_path}/{item['id']}", json=updated).status_code == 404


def test_job_fields_and_exact_contacts_across_types(client):
    definition = post(
        client, "/custom-fields", {"entity_type": "job", "label": "工作地点", "value_type": "text"}
    )
    company, candidate, job = records(client)
    response = client.patch(
        f"/api/v1/jobs/{job['id']}",
        json={
            "company_id": company["id"],
            "title": job["title"],
            "custom_fields": {definition["key"]: "杭州"},
        },
    )
    assert response.status_code == 200 and response.json()["custom_fields"][definition["key"]] == "杭州"
    post(
        client,
        "/candidates",
        {"name": "类型不同但内容相同", "contact_methods": [{"type": "phone", "value": "001234"}]},
    )
    batch = preview(
        client,
        upload(client, [["姓名", "联系方式"], ["原文联系方式", "001234"]]),
        {"0": "name", "1": "contact:other"},
    )
    assert batch["counts"]["review"] == 1


def test_limits_and_reupload_history(client):
    batch = upload(client, [["姓名"], ["重复文件合成"]])
    again = upload(client, [["姓名"], ["重复文件合成"]])
    assert again["previous_batches"] == [batch["id"]]
    large = upload(client, [["姓名"]] + [[f"合成{i}"] for i in range(5001)])
    response = client.post(
        f"/api/v1/imports/{large['id']}/preview",
        json={
            "revision": 0,
            "sheet_name": "CSV",
            "header_row": 1,
            "mapping": {"0": "name"},
        },
    )
    assert response.status_code == 422
    assert rows_of(client, large) == []
    data = ("x" * (10 * 1024 * 1024 + 1)).encode()
    assert client.post("/api/v1/imports/upload", files={"file": ("oversized.csv", data)}).status_code == 413
