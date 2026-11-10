"""SQLite persistente, uma conexão por contexto e transações por operação."""
import sqlite3
from datetime import datetime, timezone

from flask import current_app, g, request
from werkzeug.security import generate_password_hash

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY AUTOINCREMENT, cpf TEXT UNIQUE NOT NULL,
 name TEXT NOT NULL, password_hash TEXT NOT NULL,
 role TEXT NOT NULL CHECK(role IN ('administrador','fiscalizador')),
 orgao TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1, auth_version INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS processes (
 id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT UNIQUE NOT NULL,
 orgao TEXT NOT NULL, objeto TEXT NOT NULL, prazo TEXT NOT NULL,
 status TEXT NOT NULL, risco TEXT NOT NULL, modalidade TEXT NOT NULL,
 percentual INTEGER NOT NULL CHECK(percentual BETWEEN 0 AND 100),
 etapa TEXT NOT NULL, responsavel TEXT NOT NULL,
 valor_centavos INTEGER NOT NULL CHECK(valor_centavos >= 0),
 ocorrencia TEXT NOT NULL, encaminhamento TEXT NOT NULL,
 created_by INTEGER NOT NULL REFERENCES users(id),
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 version INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS attachments (
 id TEXT PRIMARY KEY, process_id INTEGER NOT NULL REFERENCES processes(id),
 original_name TEXT NOT NULL, stored_name TEXT UNIQUE NOT NULL,
 size INTEGER NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reports (
 id INTEGER PRIMARY KEY AUTOINCREMENT, period TEXT NOT NULL,
 scope TEXT NOT NULL, author_id INTEGER NOT NULL REFERENCES users(id),
 content TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER REFERENCES users(id),
 event TEXT NOT NULL, process_id INTEGER REFERENCES processes(id),
 ip TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS login_attempts (ip TEXT NOT NULL, attempted_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS recovery_requests (
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER REFERENCES users(id),
 email TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_processes_orgao ON processes(orgao);
CREATE INDEX IF NOT EXISTS idx_attachments_process ON attachments(process_id);
CREATE INDEX IF NOT EXISTS idx_attempts_ip ON login_attempts(ip, attempted_at);
"""


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"], timeout=15)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.execute("PRAGMA busy_timeout = 15000")
    return g.db


def close_db(error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_db():
    db = get_db()
    db.execute("PRAGMA journal_mode = WAL")
    db.executescript(SCHEMA)
    db.commit()


def create_user(cpf, name, password, role, orgao):
    from .constants import ORGAOS
    cpf = "".join(c for c in cpf if c.isascii() and c.isdigit())
    if len(cpf) != 11 or not name.strip() or len(name.strip()) > 120:
        raise ValueError("Informe um identificador de 11 dígitos e um nome válido.")
    if not 12 <= len(password) <= 128:
        raise ValueError("A senha deve ter entre 12 e 128 caracteres.")
    if role not in {"administrador", "fiscalizador"} or orgao not in ORGAOS:
        raise ValueError("Perfil ou órgão inválido.")
    if role == "fiscalizador" and orgao == ORGAOS[0]:
        raise ValueError("Vincule o fiscalizador a um órgão específico.")
    cursor = get_db().execute(
        "INSERT INTO users(cpf,name,password_hash,role,orgao,created_at) VALUES(?,?,?,?,?,?)",
        (cpf, name.strip(), generate_password_hash(password), role, orgao, now()),
    )
    return cursor.lastrowid


def event(action, process_id=None):
    user = g.get("user")
    get_db().execute(
        "INSERT INTO events(user_id,event,process_id,ip,created_at) VALUES(?,?,?,?,?)",
        (user["id"] if user else None, action, process_id, request.remote_addr or "", now()),
    )
