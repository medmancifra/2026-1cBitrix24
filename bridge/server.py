#!/usr/bin/env python3
"""
Bitrix24 Bridge Server
======================
A simple HTTP bridge that exposes the Python boilerplate core + bundles
as a REST API for the Quarkus HeroUI microservice (Phase 2).

This server runs alongside the Quarkus stand and provides the data layer.
The Quarkus microservice calls this bridge to retrieve Bitrix24 data.

Usage:
    python bridge/server.py

Environment variables:
    BX24_DOMAIN, BX24_USER_ID, BX24_WEBHOOK_TOKEN (or OAuth2 vars)
    BRIDGE_HOST (default: 0.0.0.0)
    BRIDGE_PORT (default: 5000)

Endpoints (all return JSON):
    GET  /api/v1/health
    GET  /api/v1/bundles/status
    GET  /api/v1/kanban/{entity_type}/board
    POST /api/v1/kanban/{entity_type}/cards/{task_id}/move?stage_id=N
    GET  /api/v1/smart/types
    GET  /api/v1/smart/{entity_type_id}/state
    POST /api/v1/smart/{entity_type_id}/items
    POST /api/v1/smart/{entity_type_id}/items/{item_id}/move?stage_id=S
    GET  /api/v1/bp/workflows
    POST /api/v1/bp/workflows/start
    POST /api/v1/bp/workflows/{workflow_id}/pause
    POST /api/v1/bp/workflows/{workflow_id}/stop
    DELETE /api/v1/bp/workflows/{workflow_id}
"""

import json
import os
import sys
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import Bitrix24Client, WebhookAuth, OAuth2Auth
from core.exceptions import Bitrix24Error
from bundles.kanban.board import KanbanBoard
from bundles.smart_processes.process import SmartProcess

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("bridge")

HOST = os.environ.get("BRIDGE_HOST", "0.0.0.0")
PORT = int(os.environ.get("BRIDGE_PORT", "5000"))


def get_client():
    return Bitrix24Client.from_env()


def json_response(handler, data, status=200):
    body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", len(body))
    handler.end_headers()
    handler.wfile.write(body)


def error_response(handler, message, status=500):
    json_response(handler, {"success": False, "error": message}, status)


class BridgeHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        log.info("%s - %s", self.address_string(), format % args)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        qs = parse_qs(parsed.query)

        try:
            client = get_client()

            # Health
            if path == "/api/v1/health":
                json_response(self, {"status": "ok", "bridge": "running"})

            # All bundle statuses
            elif path == "/api/v1/bundles/status":
                statuses = []
                kb = KanbanBoard(client, entity_type=1)
                statuses.append(kb.get_health_status())
                sp = SmartProcess(client)
                statuses.append(sp.get_health_status())
                json_response(self, statuses)

            # Kanban board
            elif path.startswith("/api/v1/kanban/") and path.endswith("/board"):
                parts = path.split("/")
                entity_type = int(parts[4])
                kb = KanbanBoard(client, entity_type=entity_type)
                state = kb.get_board_state()
                json_response(self, state.to_dict())

            # Smart process types
            elif path == "/api/v1/smart/types":
                sp = SmartProcess(client)
                types = sp.list_types()
                json_response(self, [t.to_dict() for t in types])

            # Smart process state
            elif path.startswith("/api/v1/smart/") and path.endswith("/state"):
                parts = path.split("/")
                entity_type_id = int(parts[4])
                sp = SmartProcess(client)
                state = sp.get_process_state(entity_type_id)
                json_response(self, state)

            # BP workflows
            elif path == "/api/v1/bp/workflows":
                sp = SmartProcess(client)
                workflows = sp.list_workflows()
                json_response(self, workflows)

            else:
                error_response(self, f"Not found: {path}", 404)

        except Bitrix24Error as e:
            error_response(self, str(e), 502)
        except Exception as e:
            log.exception("Unexpected error: %s", e)
            error_response(self, str(e), 500)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        qs = parse_qs(parsed.query)

        content_length = int(self.headers.get("Content-Length", 0))
        body = {}
        if content_length > 0:
            try:
                body = json.loads(self.rfile.read(content_length))
            except json.JSONDecodeError:
                body = {}

        try:
            client = get_client()

            # Move Kanban card
            if "/cards/" in path and path.endswith("/move"):
                parts = path.split("/")
                entity_type = int(parts[4])
                task_id = int(parts[6])
                stage_id = int(qs.get("stage_id", [0])[0])
                kb = KanbanBoard(client, entity_type=entity_type)
                result = kb.move_card(task_id, stage_id)
                json_response(self, {"success": True, "data": result})

            # Add Smart Process item
            elif path.startswith("/api/v1/smart/") and path.endswith("/items"):
                entity_type_id = int(path.split("/")[4])
                sp = SmartProcess(client)
                item = sp.add_item(
                    entity_type_id=entity_type_id,
                    title=body.get("title", ""),
                    stage_id=body.get("stage_id"),
                    assigned_by_id=body.get("assigned_by_id"),
                    extra_fields={k: v for k, v in body.items()
                                  if k not in ("title", "stage_id", "assigned_by_id")},
                )
                json_response(self, item.to_dict(), 201)

            # Move Smart Process item
            elif "/items/" in path and path.endswith("/move"):
                parts = path.split("/")
                entity_type_id = int(parts[4])
                item_id = int(parts[6])
                stage_id = qs.get("stage_id", [""])[0]
                sp = SmartProcess(client)
                result = sp.move_item_to_stage(item_id, entity_type_id, stage_id)
                json_response(self, {"success": True, "data": result})

            # Start BP workflow
            elif path == "/api/v1/bp/workflows/start":
                sp = SmartProcess(client)
                wf_id = sp.start_workflow(
                    item_id=body.get("item_id"),
                    entity_type_id=body.get("entity_type_id"),
                    template_id=body.get("template_id"),
                    parameters=body.get("parameters"),
                )
                json_response(self, {"success": True, "data": wf_id}, 201)

            # Pause workflow
            elif "/workflows/" in path and path.endswith("/pause"):
                workflow_id = path.split("/")[-2]
                sp = SmartProcess(client)
                result = sp.pause_workflow(workflow_id)
                json_response(self, {"success": True, "data": result})

            # Stop workflow
            elif "/workflows/" in path and path.endswith("/stop"):
                workflow_id = path.split("/")[-2]
                sp = SmartProcess(client)
                result = sp.stop_workflow(workflow_id)
                json_response(self, {"success": True, "data": result})

            else:
                error_response(self, f"Not found: {path}", 404)

        except Bitrix24Error as e:
            error_response(self, str(e), 502)
        except Exception as e:
            log.exception("Unexpected error: %s", e)
            error_response(self, str(e), 500)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        try:
            client = get_client()

            # Delete workflow
            if "/workflows/" in path:
                workflow_id = path.split("/")[-1]
                sp = SmartProcess(client)
                result = sp.delete_workflow(workflow_id)
                json_response(self, {"success": True, "data": result})
            else:
                error_response(self, f"Not found: {path}", 404)

        except Bitrix24Error as e:
            error_response(self, str(e), 502)
        except Exception as e:
            log.exception("Unexpected error: %s", e)
            error_response(self, str(e), 500)


def main():
    server = HTTPServer((HOST, PORT), BridgeHandler)
    log.info("Bitrix24 Bridge Server started on http://%s:%d", HOST, PORT)
    log.info("API docs: see Manuals.md for endpoint reference")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Shutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
