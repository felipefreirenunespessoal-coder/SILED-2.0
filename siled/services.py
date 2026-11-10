import json
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from flask import abort, current_app, g, url_for

from .constants import MODALITIES, ORGAOS, RISKS, STATUS
from .db import get_db


def scope_clause():
    return ("1=1", []) if g.user["role"] == "administrador" else ("orgao=?", [g.user["orgao"]])


def list_processes():
    clause, args = scope_clause()
    rows = [dict(r) for r in get_db().execute(f"SELECT * FROM processes WHERE {clause} ORDER BY id DESC", args)]
    files = get_db().execute(f"SELECT a.* FROM attachments a JOIN processes p ON p.id=a.process_id WHERE {'1=1' if g.user['role']=='administrador' else 'p.orgao=?'} ORDER BY a.created_at", args).fetchall()
    grouped = {}
    for attachment in files:
        grouped.setdefault(attachment["process_id"], []).append(dict(attachment))
    for row in rows:
        row["arquivos"] = grouped.get(row["id"], [])
    return rows


def get_process(process_id):
    row = get_db().execute("SELECT * FROM processes WHERE id=?", (process_id,)).fetchone()
    if row is None:
        abort(404, description="Processo não encontrado.")
    if g.user["role"] != "administrador" and row["orgao"] != g.user["orgao"]:
        abort(403, description="Este processo pertence a outro órgão.")
    return dict(row)


def money_to_cents(value):
    text = str(value or "").strip().replace("R$", "").replace(" ", "")
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        number = Decimal(text or "0")
        if not number.is_finite() or number < 0 or number > Decimal("999999999999.99"):
            raise ValueError
        return int((number * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    except (InvalidOperation, ValueError, OverflowError):
        raise ValueError("Informe um valor estimado válido, não negativo e com até 12 dígitos inteiros.") from None


def parse_process(form):
    def text(key, maximum=200, required=False, default=""):
        value = str(form.get(key, "")).strip() or default
        if (required and not value) or len(value) > maximum:
            raise ValueError(f"Confira o campo {key}; limite de {maximum} caracteres.")
        return value
    orgao = text("orgao", 200, True)
    if orgao not in ORGAOS:
        raise ValueError("Selecione um órgão válido.")
    if g.user["role"] != "administrador" and orgao != g.user["orgao"]:
        abort(403, description="Você só pode cadastrar processos do seu órgão.")
    status, risco, modalidade = text("status", default=STATUS[0]), text("risco", default=RISKS[0]), text("modalidade", default=MODALITIES[0])
    if status not in STATUS or risco not in RISKS or modalidade not in MODALITIES:
        raise ValueError("Selecione status, risco e modalidade válidos.")
    prazo = text("prazo", 10, True)
    try:
        date.fromisoformat(prazo)
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", prazo):
            raise ValueError
        percentual = int(form.get("percentual", "0") or 0)
        if not 0 <= percentual <= 100:
            raise ValueError
    except ValueError:
        raise ValueError("Informe uma data válida e um percentual entre 0 e 100.") from None
    codigo = text("codigo", 80)
    if codigo and not re.fullmatch(r"[A-Za-z0-9._/-]+", codigo):
        raise ValueError("Use letras, números, ponto, barra, hífen ou sublinhado no código.")
    return dict(codigo=codigo, orgao=orgao, objeto=text("objeto", 1000, True), prazo=prazo,
                status=status, risco=risco, modalidade=modalidade, percentual=percentual,
                etapa=text("etapa", default="Triagem inicial"), responsavel=text("responsavel", default="Não informado"),
                valor_centavos=money_to_cents(form.get("valor")), ocorrencia=text("ocorrencia", 4000), encaminhamento=text("encaminhamento", 4000))


def metrics(rows):
    return dict(total=len(rows), concluidos=sum(p["status"] == "Concluído" for p in rows),
                acompanhamento=sum(p["status"] == "Em acompanhamento" for p in rows),
                alertas=sum(p["status"] == "Em alerta" for p in rows),
                arquivos_total=sum(len(p["arquivos"]) for p in rows), valor_total=sum(p["valor_centavos"] for p in rows))


def report_period(value=None):
    value = value or datetime.now(ZoneInfo("America/Porto_Velho")).strftime("%Y-%m")
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value) or int(value[:4]) < 2000:
        raise ValueError("Selecione um mês válido.")
    return value


def month_rows(rows, period):
    return [p for p in rows if datetime.fromisoformat(p["updated_at"]).astimezone(ZoneInfo("America/Porto_Velho")).strftime("%Y-%m") == period]


def report_sections(rows, period):
    m = metrics(rows)
    return [
        {"title": "Panorama geral", "lines": [f"Processos atualizados no mês {period[5:]}/{period[:4]}: {m['total']}.", f"Processos concluídos: {m['concluidos']}. Arquivos anexados: {m['arquivos_total']}."] if rows else ["Não há processos atualizados para o período selecionado.", "O relatório será consolidado assim que houver registros no período."]},
        {"title": "Alertas do mês", "lines": [f"Processos em alerta: {m['alertas']}.", f"Processos em acompanhamento: {m['acompanhamento']}."] if rows else ["Não há alertas registrados no momento.", "Não há pendências em acompanhamento."]},
        {"title": "Encaminhamentos", "lines": ["Atualizar os processos em alerta com o órgão responsável.", "Validar a documentação e revisar os prazos do período.", "Registrar as providências adotadas e gerar novamente o relatório."] if rows else ["Cadastre os processos que serão acompanhados.", "Vincule os documentos correspondentes.", "Gere o relatório mensal após a inclusão dos dados."]},
    ]


def plain_report(sections):
    return "\n\n".join(section["title"] + ":\n" + "\n".join("- " + line for line in section["lines"]) for section in sections)


def powerbi_config():
    value = current_app.config["POWERBI_EMBED_URL"].strip()
    try:
        parsed = urlsplit(value)
        valid = parsed.scheme == "https" and parsed.hostname in {"app.powerbi.com", "app.powerbigov.us", "msit.powerbi.com"} and not parsed.username and not parsed.password and parsed.port in (None, 443)
    except ValueError:
        valid = False
    return {"enabled": bool(value and valid), "configuration_error": bool(value and not valid), "embed_url": value if valid else "", "title": current_app.config["POWERBI_REPORT_TITLE"], "workspace_name": current_app.config["POWERBI_WORKSPACE_NAME"]}
