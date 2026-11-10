"""Inicialização local ou em hospedagem com Waitress."""
import argparse
import os
import threading
import time
import urllib.error
import urllib.request
import webbrowser

from waitress import serve
from siled import create_app


def open_when_ready(url):
    for _ in range(50):
        try:
            with urllib.request.urlopen(url + "/healthz", timeout=1) as response:
                if response.status == 200:
                    webbrowser.open(url)
                    return
        except (OSError, urllib.error.URLError):
            time.sleep(0.2)


def main():
    parser = argparse.ArgumentParser(description="Servidor SILED Estratégico")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--open-browser", action="store_true")
    args = parser.parse_args()
    app = create_app()
    host = args.host or os.getenv("HOST", "127.0.0.1")
    port = args.port if args.port is not None else int(os.getenv("PORT", "5000"))
    if not 1 <= port <= 65535:
        parser.error("A porta deve estar entre 1 e 65535.")
    browser_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    url = f"http://{browser_host}:{port}"
    if args.open_browser:
        threading.Thread(target=open_when_ready, args=(url,), daemon=True).start()
    print(f"SILED em {url} | interface {host}:{port}", flush=True)
    serve(app, host=host, port=port, threads=4)


if __name__ == "__main__":
    main()
