"""Administração local. Senhas são solicitadas no terminal, nunca em argumentos."""
import argparse
import getpass
import re
import sqlite3

from werkzeug.security import generate_password_hash
from siled import create_app
from siled.constants import ORGAOS
from siled.db import create_user, get_db


def choose_orgao(text, role):
    if role == "administrador":
        return ORGAOS[0]
    if text:
        matches = [o for o in ORGAOS[1:] if o == text or o.startswith(text.upper() + " -")]
        if len(matches) == 1:
            return matches[0]
        raise ValueError("Órgão não encontrado. Informe a sigla, como SESAU ou SEFIN.")
    for index, orgao in enumerate(ORGAOS[1:], 1):
        print(f"{index:2}. {orgao}")
    index = int(input("Número do órgão: "))
    if not 1 <= index < len(ORGAOS):
        raise ValueError("Número de órgão inválido.")
    return ORGAOS[index]


def read_password():
    password = getpass.getpass("Senha (12 a 128 caracteres): ")
    if not 12 <= len(password) <= 128:
        raise ValueError("A senha deve ter entre 12 e 128 caracteres.")
    if password != getpass.getpass("Confirme a senha: "):
        raise ValueError("As senhas não conferem.")
    return password


def main():
    parser = argparse.ArgumentParser(description="Administração do SILED")
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create-user", help="Cadastrar usuário")
    create.add_argument("--role", choices=["administrador", "fiscalizador"], default="administrador")
    create.add_argument("--orgao", help="Sigla do órgão para fiscalizador")
    commands.add_parser("reset-password", help="Redefinir senha e encerrar sessões do usuário")
    commands.add_parser("has-users", help="Retorna 0 com usuários, 1 sem usuários e 2 em caso de erro")
    commands.add_parser("status", help="Contagens gerais do banco")
    args = parser.parse_args()
    app = create_app()
    with app.app_context():
        db = get_db()
        if args.command == "has-users":
            return 0 if db.execute("SELECT 1 FROM users LIMIT 1").fetchone() else 1
        if args.command == "status":
            for table, label in [("users", "Usuários"), ("processes", "Processos"), ("attachments", "Anexos"), ("reports", "Relatórios")]:
                print(f"{label}: {db.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]}")
            return 0
        try:
            cpf = re.sub(r"[^0-9]", "", input("CPF do usuário (11 dígitos): "))
            if args.command == "create-user":
                name = input("Nome do usuário: ").strip()
                orgao = choose_orgao(args.orgao, args.role)
                password = read_password()
                create_user(cpf, name, password, args.role, orgao)
                db.commit()
                print("Usuário cadastrado. Nenhuma senha foi exibida ou gravada em texto simples.")
            else:
                if not db.execute("SELECT id FROM users WHERE cpf=?", (cpf,)).fetchone():
                    raise ValueError("Usuário não encontrado.")
                password = read_password()
                db.execute("UPDATE users SET password_hash=?,auth_version=auth_version+1 WHERE cpf=?", (generate_password_hash(password), cpf))
                db.commit()
                print("Senha redefinida. Sessões anteriores desse usuário foram invalidadas.")
        except (ValueError, sqlite3.IntegrityError) as error:
            db.rollback()
            print("Erro: CPF já cadastrado." if isinstance(error, sqlite3.IntegrityError) else f"Erro: {error}")
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
