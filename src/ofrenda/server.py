"""Local server for Ofrenda: The Ghost in the Machine.

Serves the interactive Altar memorial UI and routes live forensic queries
to the Gemma 2B archive inference runtime with BM25 citation grounding.
"""

from __future__ import annotations

import json
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .ask import DEFAULT_MODEL, ask_ghost
from .index import build_corpse_index

ALTAR_DIR = Path(__file__).resolve().parents[2] / "altar"


class AltarHandler(SimpleHTTPRequestHandler):
    index = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ALTAR_DIR), **kwargs)

    def do_GET(self):
        if self.path == "/healthz":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "ok", "service": "ofrenda-altar"}')
            return
        super().do_GET()

    def do_POST(self):
        if self.path == "/api/ask":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body.decode("utf-8"))
                question = data.get("question", "").strip()
            except Exception:
                question = ""

            if not question:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error": "Question is required"}')
                return

            if AltarHandler.index is None:
                AltarHandler.index = build_corpse_index()

            try:
                threshold = 1.0 if len(AltarHandler.index.documents) < 100 else 6.0
                res = ask_ghost(question, AltarHandler.index, model="gemma:2b", top_k=3, score_threshold=threshold)
            except Exception as e:
                res = {
                    "question": question,
                    "answer": f"The archive is silent on that. (Error: {e})",
                    "citations": [],
                    "abstention": True,
                }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))
        else:
            self.send_error(404, "Not Found")

    def end_headers(self):
        # Prevent aggressive caching in local development
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


def run_server(host: str = "0.0.0.0", port: int = 8080):
    print(f"Pre-loading corpse archival index over request/request...")
    AltarHandler.index = build_corpse_index()
    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, AltarHandler)
    print(f"\n✨ OFRENDA: The Ghost in the Machine is live on {host}:{port}!")
    print(f"🕯️  Altar Memorial UI: http://{host}:{port}")
    print(f"👻 Forensic Interview API: http://{host}:{port}/api/ask\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nAltar server stopped.")


if __name__ == "__main__":
    port_env = os.environ.get("PORT")
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    elif port_env:
        port = int(port_env)
    else:
        port = 8080
    host = os.environ.get("HOST", "0.0.0.0")
    run_server(host=host, port=port)
