import os
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from flask import Flask, abort, g, render_template, request, session
from werkzeug.middleware.proxy_fix import ProxyFix

from . import db


def create_app(test_config=None):
    root = Path(__file__).resolve().parent.parent
    load_dotenv(root / ".env", override=False)
    app = Flask(__name__, instance_path=str(root / "instance"))
    app.config.from_mapping(
        DATA_DIR=os.getenv("SILED_DATA_DIR") or str(root / "instance"),
        SECRET_KEY=os.getenv("FLASK_SECRET_KEY", ""),
        PRODUCTION=os.getenv("SILED_ENV", "local") == "production",
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8), MAX_CONTENT_LENGTH=25 * 1024 * 1024,
        MAX_FORM_PARTS=100, MAX_FORM_MEMORY_SIZE=256 * 1024,
        POWERBI_EMBED_URL=os.getenv("POWERBI_EMBED_URL", ""),
        POWERBI_REPORT_TITLE=os.getenv("POWERBI_REPORT_TITLE", "Painel Microsoft Power BI"),
        POWERBI_WORKSPACE_NAME=os.getenv("POWERBI_WORKSPACE_NAME", "Unidade central"),
        TRUST_PROXY=os.getenv("TRUST_PROXY", "0") == "1",
    )
    if test_config:
        app.config.update(test_config)
    data = Path(app.config["DATA_DIR"]).resolve()
    data.mkdir(parents=True, exist_ok=True)
    if app.config["PRODUCTION"] and len(app.config["SECRET_KEY"]) < 32:
        raise RuntimeError("Defina FLASK_SECRET_KEY aleatória com ao menos 32 caracteres para produção.")
    if not app.config["SECRET_KEY"]:
        key_file = data / ".secret_key"
        try:
            descriptor = os.open(key_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "w") as handle:
                handle.write(secrets.token_hex(32))
        except FileExistsError:
            pass
        app.config["SECRET_KEY"] = key_file.read_text().strip()
    app.config["SESSION_COOKIE_SECURE"] = app.config["PRODUCTION"]
    app.config.setdefault("DATABASE", str(data / "siled.sqlite3"))
    app.config["UPLOAD_DIR"] = data / "uploads"
    app.config["UPLOAD_DIR"].mkdir(exist_ok=True)
    if app.config["TRUST_PROXY"]:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
    app.teardown_appcontext(db.close_db)
    with app.app_context():
        db.init_db()
        if not app.config.get("TESTING") and not db.get_db().execute("SELECT 1 FROM users LIMIT 1").fetchone():
            cpf, password = os.getenv("SILED_ADMIN_CPF", ""), os.getenv("SILED_ADMIN_PASSWORD", "")
            if cpf and password:
                from .constants import ORGAOS
                db.create_user(cpf, os.getenv("SILED_ADMIN_NAME") or "Administrador", password, "administrador", ORGAOS[0])
                db.get_db().commit()

    @app.before_request
    def load_identity_and_protect_forms():
        g.user = None
        if session.get("user_id"):
            g.user = db.get_db().execute("SELECT * FROM users WHERE id=? AND active=1", (session["user_id"],)).fetchone()
            if g.user is None or session.get("auth_version") != g.user["auth_version"]:
                session.clear()
                g.user = None
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            expected = session.get("csrf_token", "")
            actual = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token", "")
            if not expected or not actual or not secrets.compare_digest(expected.encode(), actual.encode()):
                abort(400, description="A sessão do formulário expirou. Recarregue a página e tente novamente.")

    @app.context_processor
    def common_context():
        session.setdefault("csrf_token", secrets.token_urlsafe(32))
        return {"csrf_token": session["csrf_token"], "app_title": "SILED Estratégico"}

    @app.template_filter("currency_br")
    def currency_br(cents):
        value = int(cents or 0) / 100
        return (f"R$ {value:,.2f}").replace(",", "X").replace(".", ",").replace("X", ".")

    @app.template_filter("localdate")
    def localdate(value):
        if not value:
            return "—"
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo:
            parsed = parsed.astimezone(ZoneInfo("America/Porto_Velho"))
        return parsed.strftime("%d/%m/%Y %H:%M")

    @app.template_filter("date_br")
    def date_br(value):
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d/%m/%Y") if value else "—"

    @app.after_request
    def response_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
            "frame-src https://app.powerbi.com https://app.powerbigov.us https://msit.powerbi.com; "
            "object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
        )
        if request.endpoint != "static":
            response.headers["Cache-Control"] = "no-store"
        if app.config["PRODUCTION"]:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response

    for status in (400, 403, 404, 409, 413, 429, 500):
        def handle_error(error):
            description = "Não foi possível concluir a operação." if error.code == 500 else error.description
            if error.code == 413:
                description = "Os anexos ultrapassam o limite de 25 MB por envio."
            return render_template("error.html", code=error.code, message=description), error.code
        app.register_error_handler(status, handle_error)
    from .views import bp
    app.register_blueprint(bp)
    return app
