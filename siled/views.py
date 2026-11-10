import csv
import io
import json
import re
import secrets
import sqlite3
import time
import uuid
from datetime import datetime
from functools import wraps
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from flask import Blueprint, Response, abort, current_app, flash, g, jsonify, redirect, render_template, request, send_from_directory, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from .constants import BOARD, EXTENSIONS, MODALITIES, ORGAOS, RISKS, STATUS
from .db import create_user, event, get_db, now
from .services import get_process, list_processes, metrics, month_rows, parse_process, plain_report, powerbi_config, report_period, report_sections

bp = Blueprint("web", __name__)
DUMMY_PASSWORD_HASH = generate_password_hash(secrets.token_urlsafe(24))


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("web.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def dashboard_context(active_view, form=None, edit=None, sections=None, period=None):
    rows = list_processes()
    scope = "all" if g.user["role"] == "administrador" else g.user["orgao"]
    period = report_period(period)
    latest = get_db().execute("SELECT * FROM reports WHERE scope=? AND period=? ORDER BY id DESC LIMIT 1", (scope, period)).fetchone()
    groups = [{"status": s, "title": t, "hint": h, "key": k, "items": [p for p in rows if p["status"] == s]} for s, t, h, k in BOARD]
    logs = get_db().execute("SELECT e.*,u.name,u.role FROM events e LEFT JOIN users u ON e.user_id=u.id WHERE e.event IN ('Entrada no sistema','Saída do sistema') AND (?=1 OR e.user_id=?) ORDER BY e.id DESC LIMIT 30", (int(g.user["role"] == "administrador"), g.user["id"])).fetchall()
    return dict(user=g.user, active_view=active_view, metrics=metrics(rows), processos=rows, board=groups,
                orgaos=ORGAOS if g.user["role"] == "administrador" else [g.user["orgao"]],
                status_options=STATUS, risk_options=RISKS, modality_options=MODALITIES,
                form=form or {}, edit=edit, period=period, report_metrics=metrics(month_rows(rows, period)),
                sections=sections if sections is not None else (json.loads(latest["content"]) if latest else None),
                generated_at=latest["created_at"] if latest else None, powerbi=powerbi_config(), access_log=logs,
                client_ip=request.remote_addr or "", login_at=session.get("login_at", ""))


@bp.route("/", methods=["GET", "POST"])
def login():
    if request.method == "GET" and g.user:
        return redirect(url_for("web.dashboard"))
    if request.method == "POST":
        db, ip, timestamp = get_db(), request.remote_addr or "", int(time.time())
        db.execute("DELETE FROM login_attempts WHERE attempted_at < ?", (timestamp - 900,))
        failures = db.execute("SELECT COUNT(*) FROM login_attempts WHERE ip=?", (ip,)).fetchone()[0]
        if failures >= 5:
            db.commit()
            abort(429, description="Muitas tentativas de entrada. Aguarde 15 minutos e tente novamente.")
        cpf = re.sub(r"[^0-9]", "", request.form.get("cpf", ""))
        password = request.form.get("password", "")
        user = db.execute("SELECT * FROM users WHERE cpf=? AND active=1", (cpf,)).fetchone()
        valid = check_password_hash(user["password_hash"] if user else DUMMY_PASSWORD_HASH, password[:128]) and len(password) <= 128
        selected_orgao = request.form.get("orgao", ORGAOS[0])
        if not user or not valid or selected_orgao not in ORGAOS or (user["role"] != "administrador" and selected_orgao != user["orgao"]):
            db.execute("INSERT INTO login_attempts(ip,attempted_at) VALUES(?,?)", (ip, timestamp))
            db.commit()
            flash("Confira o CPF, a senha e o órgão vinculado ao seu cadastro.", "error")
            return render_template("login.html", orgaos=ORGAOS, cpf=cpf), 401
        db.execute("DELETE FROM login_attempts WHERE ip=?", (ip,))
        session.clear()
        session.update(user_id=user["id"], auth_version=user["auth_version"], login_at=now(), csrf_token=secrets.token_urlsafe(32))
        session.permanent = True
        g.user = user
        event("Entrada no sistema")
        db.commit()
        target = request.args.get("next", "")
        parsed = urlsplit(target)
        if not target.startswith("/") or target.startswith("//") or parsed.netloc or parsed.scheme or "\\" in target:
            target = url_for("web.dashboard")
        return redirect(target)
    has_users = get_db().execute("SELECT 1 FROM users LIMIT 1").fetchone() is not None
    return render_template("login.html", orgaos=ORGAOS, has_users=has_users)


@bp.route("/recover", methods=["GET", "POST"])
def recover_password():
    submitted = False
    if request.method == "POST":
        cpf = re.sub(r"[^0-9]", "", request.form.get("cpf", ""))
        email = request.form.get("email", "").strip()
        if len(cpf) != 11 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) or len(email) > 254:
            flash("Informe CPF e e-mail válidos.", "error")
            return render_template("recover.html", submitted=False), 400
        user = get_db().execute("SELECT id FROM users WHERE cpf=? AND active=1", (cpf,)).fetchone()
        if user and get_db().execute("SELECT COUNT(*) FROM recovery_requests WHERE user_id=?", (user["id"],)).fetchone()[0] < 3:
            get_db().execute("INSERT INTO recovery_requests(user_id,email,created_at) VALUES(?,?,?)", (user["id"], email, now()))
            get_db().commit()
        submitted = True
    return render_template("recover.html", submitted=submitted)


@bp.get("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", **dashboard_context("board"))


@bp.get("/dashboard/processos")
@login_required
def dashboard_processos():
    return render_template("dashboard.html", **dashboard_context("process"))


@bp.get("/dashboard/processos/<int:process_id>/editar")
@login_required
def edit_process_form(process_id):
    item = get_process(process_id)
    item["valor"] = f"{item['valor_centavos'] / 100:.2f}".replace(".", ",")
    return render_template("dashboard.html", **dashboard_context("edit", form=item, edit=item))


def store_attachments(process_id, created_paths):
    files = [f for f in request.files.getlist("arquivos") if f.filename]
    if len(files) > 10:
        raise ValueError("Envie no máximo 10 arquivos por vez.")
    for uploaded in files:
        name = secure_filename(uploaded.filename)
        suffix = name.rsplit(".", 1)[-1].lower() if "." in name else ""
        if not name or suffix not in EXTENSIONS or len(uploaded.filename) > 200:
            raise ValueError("Anexe PDF, DOC, DOCX, XLS, XLSX, CSV, ZIP, PNG ou JPG com nome de até 200 caracteres.")
        identifier = uuid.uuid4().hex
        stored = identifier + "." + suffix
        path = current_app.config["UPLOAD_DIR"] / stored
        created_paths.append(path)
        uploaded.save(path)
        get_db().execute("INSERT INTO attachments(id,process_id,original_name,stored_name,size,created_at) VALUES(?,?,?,?,?,?)", (identifier, process_id, uploaded.filename, stored, path.stat().st_size, now()))


def save_process(existing=None):
    paths, db = [], get_db()
    try:
        values = parse_process(request.form)
        db.execute("BEGIN IMMEDIATE")
        if existing:
            try:
                version = int(request.form.get("version", "0"))
            except ValueError:
                raise ValueError("Recarregue o processo antes de salvar.") from None
            values["codigo"] = values["codigo"] or existing["codigo"]
            columns = ",".join(key + "=?" for key in values)
            cursor = db.execute(f"UPDATE processes SET {columns},updated_at=?,version=version+1 WHERE id=? AND version=?", (*values.values(), now(), existing["id"], version))
            if cursor.rowcount != 1:
                abort(409, description="Outro usuário atualizou este processo. Reabra a página para conferir a versão atual.")
            identifier = existing["id"]
        else:
            automatic = not values["codigo"]
            values["codigo"] = values["codigo"] or "PENDING-" + uuid.uuid4().hex
            columns = ",".join(values)
            placeholders = ",".join("?" for _ in values)
            cursor = db.execute(f"INSERT INTO processes({columns},created_by,created_at,updated_at) VALUES({placeholders},?,?,?)", (*values.values(), g.user["id"], now(), now()))
            identifier = cursor.lastrowid
            if automatic:
                code = f"PROC-{datetime.now(ZoneInfo('America/Porto_Velho')):%Y}-{identifier:03d}"
                if db.execute("SELECT 1 FROM processes WHERE codigo=?", (code,)).fetchone():
                    code += "-" + uuid.uuid4().hex[:6].upper()
                db.execute("UPDATE processes SET codigo=? WHERE id=?", (code, identifier))
        store_attachments(identifier, paths)
        event("Processo atualizado" if existing else "Processo cadastrado", identifier)
        db.commit()
    except (ValueError, sqlite3.IntegrityError) as error:
        db.rollback()
        for path in paths:
            path.unlink(missing_ok=True)
        message = "Este código de processo já está em uso." if isinstance(error, sqlite3.IntegrityError) else str(error)
        flash(message, "error")
        return render_template("dashboard.html", **dashboard_context("edit" if existing else "process", form=request.form.to_dict(), edit=existing)), 400
    except Exception:
        db.rollback()
        for path in paths:
            path.unlink(missing_ok=True)
        raise
    flash("Processo atualizado com sucesso." if existing else "Processo adicionado ao sistema com sucesso.", "success")
    return redirect(url_for("web.edit_process_form", process_id=identifier) if existing else url_for("web.dashboard"))


@bp.post("/processos/adicionar")
@login_required
def add_process():
    return save_process()


@bp.post("/processos/<int:process_id>/editar")
@login_required
def update_process(process_id):
    return save_process(get_process(process_id))


@bp.get("/arquivos/<attachment_id>")
@login_required
def download_file(attachment_id):
    item = get_db().execute("SELECT * FROM attachments WHERE id=?", (attachment_id,)).fetchone()
    if item is None:
        abort(404)
    get_process(item["process_id"])
    event("Anexo baixado", item["process_id"])
    get_db().commit()
    return send_from_directory(current_app.config["UPLOAD_DIR"], item["stored_name"], as_attachment=True, download_name=item["original_name"])


@bp.get("/api/processos.csv")
@login_required
def export_processes_csv():
    def cell(value):
        text = str(value)
        return "'" + text if text.lstrip().startswith(("=", "+", "-", "@")) or text.startswith(("\t", "\r", "\n")) else text
    output = io.StringIO(newline="")
    writer = csv.writer(output, delimiter=";")
    fields = ("codigo", "orgao", "objeto", "status", "risco", "etapa", "modalidade", "prazo", "responsavel", "percentual")
    writer.writerow(["Código", "Órgão", "Objeto", "Status", "Risco", "Etapa", "Modalidade", "Prazo", "Responsável", "Percentual", "Valor", "Ocorrência", "Encaminhamento", "Arquivos"])
    for item in list_processes():
        writer.writerow([cell(item[key]) for key in fields] + [f"{item['valor_centavos']/100:.2f}".replace(".", ","), cell(item["ocorrencia"]), cell(item["encaminhamento"]), cell(", ".join(f["original_name"] for f in item["arquivos"]))])
    event("Processos exportados")
    get_db().commit()
    return Response("\ufeff" + output.getvalue(), content_type="text/csv; charset=utf-8", headers={"Content-Disposition": 'attachment; filename="siled-processos.csv"'})


@bp.get("/dashboard/relatorios")
@login_required
def dashboard_relatorios():
    try:
        context = dashboard_context("report", period=request.args.get("month"))
    except ValueError as error:
        abort(400, description=str(error))
    return render_template("dashboard.html", **context)


@bp.post("/relatorios/gerar")
@bp.post("/api/monthly-report")
@login_required
def monthly_report():
    payload = request.get_json(silent=True) or request.form
    try:
        period = report_period(payload.get("month"))
    except ValueError as error:
        abort(400, description=str(error))
    sections = report_sections(month_rows(list_processes(), period), period)
    timestamp = now()
    scope = "all" if g.user["role"] == "administrador" else g.user["orgao"]
    get_db().execute("INSERT INTO reports(period,scope,author_id,content,created_at) VALUES(?,?,?,?,?)", (period, scope, g.user["id"], json.dumps(sections, ensure_ascii=False), timestamp))
    event("Relatório mensal gerado")
    get_db().commit()
    if request.path.startswith("/api/"):
        return jsonify(report=plain_report(sections), sections=sections, source="local", generated_at=timestamp, period=period)
    flash("Relatório mensal gerado e salvo.", "success")
    return redirect(url_for("web.dashboard_relatorios", month=period))


@bp.get("/dashboard/powerbi")
@login_required
def dashboard_powerbi():
    return render_template("dashboard.html", **dashboard_context("powerbi"))


@bp.route("/admin/usuarios", methods=["GET", "POST"])
@login_required
def admin_users():
    if g.user["role"] != "administrador":
        abort(403)
    if request.method == "POST":
        try:
            create_user(request.form.get("cpf", ""), request.form.get("name", ""), request.form.get("password", ""), request.form.get("role", "fiscalizador"), request.form.get("orgao", ""))
            event("Usuário cadastrado")
            get_db().commit()
            flash("Usuário cadastrado. Entregue a senha por um canal privado.", "success")
            return redirect(url_for("web.admin_users"))
        except (ValueError, sqlite3.IntegrityError) as error:
            get_db().rollback()
            flash("Este CPF já está cadastrado." if isinstance(error, sqlite3.IntegrityError) else str(error), "error")
    context = dashboard_context("users")
    context["accounts"] = get_db().execute("SELECT name,cpf,role,orgao,active FROM users ORDER BY name").fetchall()
    context["recovery_requests"] = get_db().execute("SELECT r.email,r.created_at,u.name FROM recovery_requests r JOIN users u ON u.id=r.user_id ORDER BY r.id DESC LIMIT 30").fetchall()
    return render_template("dashboard.html", **context)


@bp.post("/logout")
@login_required
def logout():
    event("Saída do sistema")
    get_db().commit()
    session.clear()
    flash("Sessão encerrada com segurança.", "success")
    return redirect(url_for("web.login"))


@bp.get("/healthz")
def health():
    get_db().execute("SELECT 1").fetchone()
    return jsonify(status="ok")
