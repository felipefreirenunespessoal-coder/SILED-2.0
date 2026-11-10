import pytest

from siled import create_app
from siled.constants import ORGAOS
from siled.db import create_user, get_db

PASSWORD = "Senha-somente-dos-testes-2026"


@pytest.fixture
def app(tmp_path):
    app = create_app({"TESTING": True, "SECRET_KEY": "chave-ficticia-isolada-dos-testes", "DATA_DIR": str(tmp_path), "PRODUCTION": False, "TRUST_PROXY": False})
    with app.app_context():
        create_user("00000000000", "Administrador de teste", PASSWORD, "administrador", ORGAOS[0])
        create_user("11111111111", "Fiscal de teste", PASSWORD, "fiscalizador", ORGAOS[18])
        create_user("22222222222", "Outro fiscal de teste", PASSWORD, "fiscalizador", ORGAOS[11])
        get_db().commit()
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def token(client):
    client.get("/")
    with client.session_transaction() as session:
        return session["csrf_token"]


def login(client, cpf="00000000000", orgao=ORGAOS[0], password=PASSWORD):
    return client.post("/", data={"cpf": cpf, "password": password, "orgao": orgao, "csrf_token": token(client)})


def post(client, url, **kwargs):
    data = kwargs.pop("data", {})
    with client.session_transaction() as session:
        data["csrf_token"] = session["csrf_token"]
    return client.post(url, data=data, **kwargs)


def process_form(**values):
    form = dict(codigo="", orgao=ORGAOS[18], objeto="Aquisição fictícia para teste", prazo="2026-12-31", status="Recebido", risco="Baixo", modalidade="Pregão Eletrônico", percentual="0", valor="1.234,56")
    form.update(values)
    return form
