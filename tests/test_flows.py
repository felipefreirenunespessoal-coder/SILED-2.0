import io
import json
from pathlib import Path

import pytest
from werkzeug.security import generate_password_hash

from siled import create_app
from siled.constants import ORGAOS
from siled.db import get_db
from siled.services import money_to_cents, report_period
from conftest import PASSWORD, login, post, process_form, token


def test_public_pages_and_authenticated_pages_render(client):
    for url in ["/", "/recover", "/healthz", "/static/css/styles.css", "/static/js/app.js"]:
        assert client.get(url).status_code == 200
    assert client.get("/dashboard").status_code == 302
    assert login(client).status_code == 302
    for url in ["/dashboard", "/dashboard/processos", "/dashboard/relatorios", "/dashboard/powerbi", "/admin/usuarios"]:
        response = client.get(url)
        assert response.status_code == 200, url
        assert b"Controle de Contratos" in response.data


def test_unregistered_user_is_rejected(client):
    assert login(client, cpf="33333333333").status_code == 401
    assert client.get("/api/processos.csv").status_code == 302


def test_wrong_password_and_wrong_organization_are_rejected(client):
    assert login(client, password="senha-incorreta").status_code == 401
    assert login(client, cpf="11111111111", orgao=ORGAOS[11]).status_code == 401


def test_login_rate_limit(client):
    for _ in range(5):
        assert login(client, password="senha-incorreta").status_code == 401
    assert login(client).status_code == 429


@pytest.mark.parametrize("bad_token", ["", "incorreto", "ç" * 10])
def test_csrf_required(client, bad_token):
    assert client.post("/", data={"cpf": "00000000000", "password": PASSWORD, "csrf_token": bad_token}).status_code == 400


def test_create_edit_and_persistence_across_app_restart(app, client):
    login(client)
    assert post(client, "/processos/adicionar", data=process_form(status="Em análise")).status_code == 302
    assert "Aquisição fictícia para teste" in client.get("/dashboard").get_data(as_text=True)
    with app.app_context():
        row = dict(get_db().execute("SELECT * FROM processes").fetchone())
        assert row["valor_centavos"] == 123456
        assert row["codigo"].startswith("PROC-")
    assert client.get(f"/dashboard/processos/{row['id']}/editar").status_code == 200
    data = process_form(codigo=row["codigo"], objeto="Objeto atualizado", status="Concluído", version=str(row["version"]))
    assert post(client, f"/processos/{row['id']}/editar", data=data).status_code == 302
    new_app = create_app({"TESTING": True, "SECRET_KEY": app.config["SECRET_KEY"], "DATA_DIR": app.config["DATA_DIR"], "PRODUCTION": False})
    with new_app.app_context():
        saved = get_db().execute("SELECT * FROM processes").fetchone()
        assert saved["objeto"] == "Objeto atualizado"
        assert saved["status"] == "Concluído"
        assert saved["version"] == 2
        assert get_db().execute("SELECT COUNT(*) FROM users").fetchone()[0] == 3


def test_stale_edit_does_not_overwrite(app, client):
    login(client)
    post(client, "/processos/adicionar", data=process_form(codigo="CONFLITO"))
    assert post(client, "/processos/1/editar", data=process_form(codigo="CONFLITO", objeto="Primeira atualização", version="1")).status_code == 302
    assert post(client, "/processos/1/editar", data=process_form(codigo="CONFLITO", objeto="Atualização antiga", version="1")).status_code == 409
    with app.app_context():
        assert get_db().execute("SELECT objeto FROM processes").fetchone()[0] == "Primeira atualização"


def test_duplicate_code_is_rejected(app, client):
    login(client)
    assert post(client, "/processos/adicionar", data=process_form(codigo="CODIGO-UNICO")).status_code == 302
    assert post(client, "/processos/adicionar", data=process_form(codigo="CODIGO-UNICO")).status_code == 400
    with app.app_context():
        assert get_db().execute("SELECT COUNT(*) FROM processes").fetchone()[0] == 1


@pytest.mark.parametrize("changes", [{"prazo": "2026-02-31"}, {"status": "Inválido"}, {"percentual": "101"}, {"valor": "NaN"}, {"valor": "-1"}, {"orgao": "Órgão inexistente"}, {"objeto": ""}])
def test_invalid_form_does_not_save(app, client, changes):
    login(client)
    assert post(client, "/processos/adicionar", data=process_form(**changes)).status_code == 400
    with app.app_context():
        assert get_db().execute("SELECT COUNT(*) FROM processes").fetchone()[0] == 0


def test_uploads_download_and_same_filename_are_preserved(app, client):
    login(client)
    for number in [1, 2]:
        assert post(client, "/processos/adicionar", data={**process_form(), "arquivos": (io.BytesIO(f"pdf fictício {number}".encode()), "documento.pdf")}, content_type="multipart/form-data").status_code == 302
    with app.app_context():
        attachments = get_db().execute("SELECT * FROM attachments ORDER BY process_id").fetchall()
        assert attachments[0]["stored_name"] != attachments[1]["stored_name"]
        assert len(list(Path(app.config["UPLOAD_DIR"]).iterdir())) == 2
    assert client.get("/arquivos/" + attachments[0]["id"]).data == "pdf fictício 1".encode()
    assert client.get("/arquivos/" + attachments[1]["id"]).data == "pdf fictício 2".encode()
    assert "attachment;" in client.get("/arquivos/" + attachments[0]["id"]).headers["Content-Disposition"]


def test_invalid_upload_rolls_back_files_and_process(app, client):
    login(client)
    data = {**process_form(), "arquivos": [(io.BytesIO(b"pdf"), "a.pdf"), (io.BytesIO(b"html"), "b.html")]}
    assert post(client, "/processos/adicionar", data=data, content_type="multipart/form-data").status_code == 400
    with app.app_context():
        assert get_db().execute("SELECT COUNT(*) FROM processes").fetchone()[0] == 0
        assert get_db().execute("SELECT COUNT(*) FROM attachments").fetchone()[0] == 0
    assert list(Path(app.config["UPLOAD_DIR"]).iterdir()) == []


def test_fiscal_cannot_access_other_org_data_files_or_admin(app, client):
    login(client)
    post(client, "/processos/adicionar", data={**process_form(orgao=ORGAOS[11], codigo="OUTRO-ORGAO"), "arquivos": (io.BytesIO(b"privado"), "documento.pdf")})
    with app.app_context():
        attachment = get_db().execute("SELECT id FROM attachments").fetchone()[0]
    post(client, "/logout")
    assert login(client, cpf="11111111111", orgao=ORGAOS[18]).status_code == 302
    assert b"OUTRO-ORGAO" not in client.get("/api/processos.csv").data
    assert client.get("/dashboard/processos/1/editar").status_code == 403
    assert client.get("/arquivos/" + attachment).status_code == 403
    assert client.get("/admin/usuarios").status_code == 403
    assert post(client, "/processos/adicionar", data=process_form(orgao=ORGAOS[11])).status_code == 403


def test_monthly_report_is_filtered_and_persisted(app, client):
    login(client)
    post(client, "/processos/adicionar", data=process_form())
    with app.app_context():
        get_db().execute("UPDATE processes SET updated_at='2026-11-01T02:00:00+00:00'")
        get_db().commit()
    october = post(client, "/api/monthly-report", data={"month": "2026-10"})
    assert october.status_code == 200
    assert "10/2026: 1" in october.json["report"]
    november = post(client, "/api/monthly-report", data={"month": "2026-11"})
    assert "Não há processos" in november.json["report"]
    with app.app_context():
        assert get_db().execute("SELECT COUNT(*) FROM reports").fetchone()[0] == 2
    assert b"Panorama geral" in client.get("/dashboard/relatorios?month=2026-10").data


def test_bad_report_period_and_csv_formula(client):
    login(client)
    assert post(client, "/api/monthly-report", data={"month": "2026-99"}).status_code == 400
    assert client.get("/dashboard/relatorios?month=abc").status_code == 400
    post(client, "/processos/adicionar", data=process_form(objeto="=1+1"))
    text = client.get("/api/processos.csv").get_data(as_text=True)
    assert ";'=1+1;" in text


def test_create_user_and_real_recovery_request(app, client):
    login(client)
    response = post(client, "/admin/usuarios", data={"cpf": "33333333333", "name": "Usuário fictício", "password": PASSWORD, "role": "fiscalizador", "orgao": ORGAOS[11]})
    assert response.status_code == 302
    post(client, "/logout")
    token(client)
    response = post(client, "/recover", data={"cpf": "33333333333", "email": "teste@example.invalid"})
    assert response.status_code == 200
    with app.app_context():
        row = get_db().execute("SELECT email FROM recovery_requests").fetchone()
        assert row["email"] == "teste@example.invalid"
        assert get_db().execute("SELECT password_hash FROM users WHERE cpf='33333333333'").fetchone()[0] != PASSWORD


def test_password_reset_invalidates_session(app, client):
    login(client)
    with app.app_context():
        get_db().execute("UPDATE users SET password_hash=?,auth_version=auth_version+1 WHERE cpf=?", (generate_password_hash("Outra-senha-ficticia-123"), "00000000000"))
        get_db().commit()
    assert client.get("/dashboard").status_code == 302


def test_security_headers_and_powerbi_allowlist(app, client):
    response = client.get("/")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "script-src 'self'" in response.headers["Content-Security-Policy"]
    login(client)
    for value in ["javascript:alert(1)", "https://example.invalid/iframe", "http://app.powerbi.com/report", "https://app.powerbi.com@evil.invalid/report"]:
        app.config["POWERBI_EMBED_URL"] = value
        assert b"<iframe" not in client.get("/dashboard/powerbi").data
    app.config["POWERBI_EMBED_URL"] = "https://app.powerbi.com/reportEmbed?reportId=teste-ficticio"
    assert b"<iframe" in client.get("/dashboard/powerbi").data


def test_missing_production_secret_is_rejected(tmp_path):
    with pytest.raises(RuntimeError, match="FLASK_SECRET_KEY"):
        create_app({"PRODUCTION": True, "SECRET_KEY": "", "DATA_DIR": str(tmp_path)})


def test_login_cannot_redirect_to_external_site(client):
    csrf = token(client)
    response = client.post("/?next=https://example.invalid", data={"cpf": "00000000000", "password": PASSWORD, "orgao": ORGAOS[0], "csrf_token": csrf})
    assert response.headers["Location"] == "/dashboard"


def test_brazilian_money_parser():
    assert money_to_cents("R$ 1.234,56") == 123456
    assert money_to_cents("1234.56") == 123456
    assert money_to_cents("0,01") == 1
    for value in ["inf", "NaN", "-0.01", "abc"]:
        with pytest.raises(ValueError):
            money_to_cents(value)
