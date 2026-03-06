#!/usr/bin/env python3
"""
bx24 — Bitrix24 Shell CLI

A command-line interface for interacting with all Bitrix24 REST API operations.
Uses the Bitrix24 core module and supports all methods documented in the
Bitrix24 Developer REST API documentation (apidocs.bitrix24.com).

Usage:
    bx24 <command> [options]
    bx24 call <method> [--param key=value ...]
    bx24 user list [--filter key=value ...]
    bx24 task list [--filter key=value ...]
    bx24 task add --title "My Task" [--responsible 1]
    bx24 crm deal list [--filter key=value ...]
    bx24 crm deal add --title "Deal" [--stage NEW]
    bx24 smart list --type-id 128
    bx24 smart add --type-id 128 --title "Item"
    bx24 bp start --template-id 1 --document crm:CCrmLead:1
    bx24 bp list
    bx24 batch --cmd "key:method?param=val" [...]
    bx24 config show
    bx24 config set <key> <value>

Environment variables:
    BX24_DOMAIN          — Bitrix24 portal domain (required)
    BX24_USER_ID         — Webhook user ID (default: 1)
    BX24_WEBHOOK_TOKEN   — Incoming webhook token
    BX24_CLIENT_ID       — OAuth2 client ID
    BX24_CLIENT_SECRET   — OAuth2 client secret
    BX24_ACCESS_TOKEN    — OAuth2 access token
    BX24_REFRESH_TOKEN   — OAuth2 refresh token
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, List

# Ensure the project root is in the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import Bitrix24Client, WebhookAuth, OAuth2Auth
from core.methods import UserMethods, TaskMethods, CRMMethods, SmartProcessMethods, BusinessProcessMethods


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        format="%(levelname)s: %(message)s",
        level=level,
    )


def print_result(result: Any, output_format: str = "pretty"):
    """Prints API result in the requested format."""
    if output_format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    elif output_format == "raw":
        print(result)
    else:
        # Pretty-print
        if isinstance(result, list):
            for i, item in enumerate(result):
                print(f"--- [{i+1}] ---")
                if isinstance(item, dict):
                    for k, v in item.items():
                        print(f"  {k}: {v}")
                else:
                    print(f"  {item}")
        elif isinstance(result, dict):
            for k, v in result.items():
                print(f"  {k}: {v}")
        else:
            print(result)


def parse_kv_params(param_list: List[str]) -> Dict[str, Any]:
    """Parses ['key=value', 'nested.key=value'] into a nested dict."""
    result = {}
    for param in (param_list or []):
        if "=" not in param:
            print(f"Warning: skipping invalid param '{param}' (no '=')", file=sys.stderr)
            continue
        key, _, value = param.partition("=")
        # Try to parse JSON values
        try:
            parsed_value = json.loads(value)
        except (json.JSONDecodeError, ValueError):
            parsed_value = value
        # Support nested keys: "fields.TITLE=Test" -> {"fields": {"TITLE": "Test"}}
        keys = key.split(".")
        target = result
        for k in keys[:-1]:
            target = target.setdefault(k, {})
        target[keys[-1]] = parsed_value
    return result


def get_client() -> Bitrix24Client:
    """Creates a Bitrix24Client from environment variables."""
    try:
        return Bitrix24Client.from_env()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Set BX24_DOMAIN and BX24_WEBHOOK_TOKEN (or OAuth2 vars) in your environment.", file=sys.stderr)
        sys.exit(1)


# ─── Command Handlers ──────────────────────────────────────────────────────────

def cmd_call(args):
    """bx24 call <method> [--param key=value ...]"""
    client = get_client()
    params = parse_kv_params(args.param)
    result = client.call(args.method, params)
    print_result(result, args.format)


def cmd_user_list(args):
    """bx24 user list [--filter key=value ...]"""
    client = get_client()
    users = UserMethods(client)
    filter_params = parse_kv_params(args.filter)
    result = users.list(filter=filter_params)
    print_result(result, args.format)


def cmd_user_get(args):
    """bx24 user get --id <user_id>"""
    client = get_client()
    users = UserMethods(client)
    result = users.get(args.id)
    print_result(result, args.format)


def cmd_user_current(args):
    """bx24 user current"""
    client = get_client()
    users = UserMethods(client)
    result = users.current()
    print_result(result, args.format)


def cmd_task_list(args):
    """bx24 task list [--filter key=value ...]"""
    client = get_client()
    tasks = TaskMethods(client)
    filter_params = parse_kv_params(args.filter)
    result = tasks.list(filter=filter_params)
    print_result(result, args.format)


def cmd_task_get(args):
    """bx24 task get --id <task_id>"""
    client = get_client()
    tasks = TaskMethods(client)
    result = tasks.get(args.id)
    print_result(result, args.format)


def cmd_task_add(args):
    """bx24 task add --title "..." [--responsible <id>] [--field key=value ...]"""
    client = get_client()
    tasks = TaskMethods(client)
    fields = parse_kv_params(args.field)
    fields["TITLE"] = args.title
    if args.responsible:
        fields["RESPONSIBLE_ID"] = args.responsible
    if args.deadline:
        fields["DEADLINE"] = args.deadline
    result = tasks.add(fields)
    print(f"Created task ID: {result}")


def cmd_task_update(args):
    """bx24 task update --id <task_id> [--field key=value ...]"""
    client = get_client()
    tasks = TaskMethods(client)
    fields = parse_kv_params(args.field)
    result = tasks.update(args.id, fields)
    print(f"Updated: {result}")


def cmd_task_delete(args):
    """bx24 task delete --id <task_id>"""
    client = get_client()
    tasks = TaskMethods(client)
    result = tasks.delete(args.id)
    print(f"Deleted: {result}")


def cmd_task_stages(args):
    """bx24 task stages [--entity-type <1|2>]"""
    client = get_client()
    tasks = TaskMethods(client)
    result = tasks.get_stages(args.entity_type)
    print_result(result, args.format)


def cmd_crm_deal_list(args):
    """bx24 crm deal list [--filter key=value ...]"""
    client = get_client()
    crm = CRMMethods(client)
    filter_params = parse_kv_params(args.filter)
    result = crm.deal_list(filter=filter_params)
    print_result(result, args.format)


def cmd_crm_deal_add(args):
    """bx24 crm deal add --title "..." [--field key=value ...]"""
    client = get_client()
    crm = CRMMethods(client)
    fields = parse_kv_params(args.field)
    fields["TITLE"] = args.title
    if args.stage:
        fields["STAGE_ID"] = args.stage
    result = crm.deal_add(fields)
    print(f"Created deal ID: {result}")


def cmd_crm_deal_get(args):
    """bx24 crm deal get --id <deal_id>"""
    client = get_client()
    crm = CRMMethods(client)
    result = crm.deal_get(args.id)
    print_result(result, args.format)


def cmd_crm_deal_update(args):
    """bx24 crm deal update --id <deal_id> [--field key=value ...]"""
    client = get_client()
    crm = CRMMethods(client)
    fields = parse_kv_params(args.field)
    result = crm.deal_update(args.id, fields)
    print(f"Updated: {result}")


def cmd_crm_deal_delete(args):
    """bx24 crm deal delete --id <deal_id>"""
    client = get_client()
    crm = CRMMethods(client)
    result = crm.deal_delete(args.id)
    print(f"Deleted: {result}")


def cmd_smart_type_list(args):
    """bx24 smart type list"""
    client = get_client()
    sp = SmartProcessMethods(client)
    result = sp.type_list()
    print_result(result, args.format)


def cmd_smart_type_add(args):
    """bx24 smart type add --title "..." [--field key=value ...]"""
    client = get_client()
    sp = SmartProcessMethods(client)
    fields = parse_kv_params(args.field)
    fields["title"] = args.title
    result = sp.type_add(fields)
    print_result(result, args.format)


def cmd_smart_list(args):
    """bx24 smart list --type-id <id> [--filter key=value ...]"""
    client = get_client()
    sp = SmartProcessMethods(client)
    filter_params = parse_kv_params(args.filter)
    result = sp.item_list(args.type_id, filter=filter_params)
    print_result(result, args.format)


def cmd_smart_add(args):
    """bx24 smart add --type-id <id> --title "..." [--field key=value ...]"""
    client = get_client()
    sp = SmartProcessMethods(client)
    fields = parse_kv_params(args.field)
    fields["title"] = args.title
    result = sp.item_add(args.type_id, fields)
    print_result(result, args.format)


def cmd_smart_get(args):
    """bx24 smart get --type-id <id> --id <item_id>"""
    client = get_client()
    sp = SmartProcessMethods(client)
    result = sp.item_get(args.type_id, args.id)
    print_result(result, args.format)


def cmd_smart_update(args):
    """bx24 smart update --type-id <id> --id <item_id> [--field key=value ...]"""
    client = get_client()
    sp = SmartProcessMethods(client)
    fields = parse_kv_params(args.field)
    result = sp.item_update(args.type_id, args.id, fields)
    print(f"Updated: {result}")


def cmd_smart_delete(args):
    """bx24 smart delete --type-id <id> --id <item_id>"""
    client = get_client()
    sp = SmartProcessMethods(client)
    result = sp.item_delete(args.type_id, args.id)
    print(f"Deleted: {result}")


def cmd_smart_stages(args):
    """bx24 smart stages --type-id <id>"""
    client = get_client()
    sp = SmartProcessMethods(client)
    result = sp.stage_list(args.type_id)
    print_result(result, args.format)


def cmd_bp_list(args):
    """bx24 bp list"""
    client = get_client()
    bp = BusinessProcessMethods(client)
    result = bp.workflow_list()
    print_result(result, args.format)


def cmd_bp_start(args):
    """bx24 bp start --template-id <id> --document <module:entity:id> [--param key=value ...]"""
    client = get_client()
    bp = BusinessProcessMethods(client)
    doc_parts = args.document.split(":")
    if len(doc_parts) != 3:
        print("Error: --document must be in format MODULE:ENTITY:ID (e.g. crm:CCrmLead:1)", file=sys.stderr)
        sys.exit(1)
    parameters = parse_kv_params(args.param)
    result = bp.workflow_start(args.template_id, doc_parts, parameters)
    print(f"Started workflow ID: {result}")


def cmd_bp_terminate(args):
    """bx24 bp terminate --workflow-id <id>"""
    client = get_client()
    bp = BusinessProcessMethods(client)
    result = bp.workflow_terminate(args.workflow_id)
    print(f"Terminated: {result}")


def cmd_bp_kill(args):
    """bx24 bp kill --workflow-id <id>"""
    client = get_client()
    bp = BusinessProcessMethods(client)
    result = bp.workflow_kill(args.workflow_id)
    print(f"Killed: {result}")


def cmd_bp_templates(args):
    """bx24 bp templates"""
    client = get_client()
    bp = BusinessProcessMethods(client)
    result = bp.template_list()
    print_result(result, args.format)


def cmd_bp_tasks(args):
    """bx24 bp tasks [--workflow-id <id>]"""
    client = get_client()
    bp = BusinessProcessMethods(client)
    result = bp.task_list(args.workflow_id)
    print_result(result, args.format)


def cmd_batch(args):
    """bx24 batch --cmd "key:method?params" [...]"""
    client = get_client()
    commands = {}
    for cmd_str in (args.cmd or []):
        if ":" not in cmd_str:
            print(f"Warning: invalid --cmd '{cmd_str}' (no ':')", file=sys.stderr)
            continue
        key, _, value = cmd_str.partition(":")
        commands[key.strip()] = value.strip()
    result = client.get_batch(commands)
    print_result(result, args.format)


def cmd_config_show(args):
    """bx24 config show — Show current configuration from env vars."""
    config = {
        "BX24_DOMAIN": os.environ.get("BX24_DOMAIN", "(not set)"),
        "BX24_USER_ID": os.environ.get("BX24_USER_ID", "1"),
        "BX24_WEBHOOK_TOKEN": ("***" if os.environ.get("BX24_WEBHOOK_TOKEN") else "(not set)"),
        "BX24_CLIENT_ID": os.environ.get("BX24_CLIENT_ID", "(not set)"),
        "BX24_ACCESS_TOKEN": ("***" if os.environ.get("BX24_ACCESS_TOKEN") else "(not set)"),
    }
    for key, value in config.items():
        print(f"  {key}={value}")


# ─── Argument Parser ───────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bx24",
        description="Bitrix24 Shell CLI — Interact with all Bitrix24 REST API methods",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  bx24 call user.current
  bx24 user list
  bx24 task list --filter "RESPONSIBLE_ID=1"
  bx24 task add --title "Fix bug" --responsible 1
  bx24 crm deal list --filter "STAGE_ID=WON"
  bx24 crm deal add --title "Big Deal" --stage NEW
  bx24 smart list --type-id 128
  bx24 smart add --type-id 128 --title "New Item"
  bx24 bp list
  bx24 bp start --template-id 5 --document crm:CCrmLead:1
  bx24 bp terminate --workflow-id abc123
  bx24 batch --cmd "u:user.get?ID=1" --cmd "d:crm.deal.list"
  bx24 config show
        """,
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    parser.add_argument("--format", "-f", choices=["pretty", "json", "raw"], default="pretty",
                        help="Output format (default: pretty)")

    sub = parser.add_subparsers(dest="command", metavar="command")
    sub.required = True

    # ── call ──
    p_call = sub.add_parser("call", help="Call any Bitrix24 REST method directly")
    p_call.add_argument("method", help="REST method name (e.g. user.get, crm.deal.list)")
    p_call.add_argument("--param", "-p", action="append", metavar="KEY=VALUE",
                        help="Method parameters (repeatable)")
    p_call.set_defaults(func=cmd_call)

    # ── user ──
    p_user = sub.add_parser("user", help="User management")
    user_sub = p_user.add_subparsers(dest="user_cmd", metavar="subcommand")
    user_sub.required = True

    pu_list = user_sub.add_parser("list", help="List users")
    pu_list.add_argument("--filter", action="append", metavar="KEY=VALUE")
    pu_list.set_defaults(func=cmd_user_list)

    pu_get = user_sub.add_parser("get", help="Get user by ID")
    pu_get.add_argument("--id", type=int, required=True)
    pu_get.set_defaults(func=cmd_user_get)

    pu_cur = user_sub.add_parser("current", help="Get current authenticated user")
    pu_cur.set_defaults(func=cmd_user_current)

    # ── task ──
    p_task = sub.add_parser("task", help="Task management")
    task_sub = p_task.add_subparsers(dest="task_cmd", metavar="subcommand")
    task_sub.required = True

    pt_list = task_sub.add_parser("list", help="List tasks")
    pt_list.add_argument("--filter", action="append", metavar="KEY=VALUE")
    pt_list.set_defaults(func=cmd_task_list)

    pt_get = task_sub.add_parser("get", help="Get task by ID")
    pt_get.add_argument("--id", type=int, required=True)
    pt_get.set_defaults(func=cmd_task_get)

    pt_add = task_sub.add_parser("add", help="Create a new task")
    pt_add.add_argument("--title", required=True)
    pt_add.add_argument("--responsible", type=int)
    pt_add.add_argument("--deadline")
    pt_add.add_argument("--field", action="append", metavar="KEY=VALUE")
    pt_add.set_defaults(func=cmd_task_add)

    pt_update = task_sub.add_parser("update", help="Update a task")
    pt_update.add_argument("--id", type=int, required=True)
    pt_update.add_argument("--field", action="append", metavar="KEY=VALUE")
    pt_update.set_defaults(func=cmd_task_update)

    pt_del = task_sub.add_parser("delete", help="Delete a task")
    pt_del.add_argument("--id", type=int, required=True)
    pt_del.set_defaults(func=cmd_task_delete)

    pt_stages = task_sub.add_parser("stages", help="List Kanban/Planner stages")
    pt_stages.add_argument("--entity-type", type=int, default=1,
                           help="Entity type: 1=My tasks, 2=Group tasks")
    pt_stages.set_defaults(func=cmd_task_stages)

    # ── crm ──
    p_crm = sub.add_parser("crm", help="CRM management")
    crm_sub = p_crm.add_subparsers(dest="crm_entity", metavar="entity")
    crm_sub.required = True

    # crm deal
    p_deal = crm_sub.add_parser("deal", help="CRM deals")
    deal_sub = p_deal.add_subparsers(dest="deal_cmd", metavar="subcommand")
    deal_sub.required = True

    pd_list = deal_sub.add_parser("list", help="List deals")
    pd_list.add_argument("--filter", action="append", metavar="KEY=VALUE")
    pd_list.set_defaults(func=cmd_crm_deal_list)

    pd_get = deal_sub.add_parser("get", help="Get deal by ID")
    pd_get.add_argument("--id", type=int, required=True)
    pd_get.set_defaults(func=cmd_crm_deal_get)

    pd_add = deal_sub.add_parser("add", help="Create a deal")
    pd_add.add_argument("--title", required=True)
    pd_add.add_argument("--stage")
    pd_add.add_argument("--field", action="append", metavar="KEY=VALUE")
    pd_add.set_defaults(func=cmd_crm_deal_add)

    pd_update = deal_sub.add_parser("update", help="Update a deal")
    pd_update.add_argument("--id", type=int, required=True)
    pd_update.add_argument("--field", action="append", metavar="KEY=VALUE")
    pd_update.set_defaults(func=cmd_crm_deal_update)

    pd_del = deal_sub.add_parser("delete", help="Delete a deal")
    pd_del.add_argument("--id", type=int, required=True)
    pd_del.set_defaults(func=cmd_crm_deal_delete)

    # ── smart (Smart Processes) ──
    p_smart = sub.add_parser("smart", help="Smart Process (Universal CRM Items) management")
    smart_sub = p_smart.add_subparsers(dest="smart_cmd", metavar="subcommand")
    smart_sub.required = True

    ps_tlist = smart_sub.add_parser("type-list", help="List smart process types")
    ps_tlist.set_defaults(func=cmd_smart_type_list)

    ps_tadd = smart_sub.add_parser("type-add", help="Create a smart process type")
    ps_tadd.add_argument("--title", required=True)
    ps_tadd.add_argument("--field", action="append", metavar="KEY=VALUE")
    ps_tadd.set_defaults(func=cmd_smart_type_add)

    ps_list = smart_sub.add_parser("list", help="List items in a smart process")
    ps_list.add_argument("--type-id", type=int, required=True)
    ps_list.add_argument("--filter", action="append", metavar="KEY=VALUE")
    ps_list.set_defaults(func=cmd_smart_list)

    ps_add = smart_sub.add_parser("add", help="Create item in smart process")
    ps_add.add_argument("--type-id", type=int, required=True)
    ps_add.add_argument("--title", required=True)
    ps_add.add_argument("--field", action="append", metavar="KEY=VALUE")
    ps_add.set_defaults(func=cmd_smart_add)

    ps_get = smart_sub.add_parser("get", help="Get smart process item")
    ps_get.add_argument("--type-id", type=int, required=True)
    ps_get.add_argument("--id", type=int, required=True)
    ps_get.set_defaults(func=cmd_smart_get)

    ps_update = smart_sub.add_parser("update", help="Update smart process item")
    ps_update.add_argument("--type-id", type=int, required=True)
    ps_update.add_argument("--id", type=int, required=True)
    ps_update.add_argument("--field", action="append", metavar="KEY=VALUE")
    ps_update.set_defaults(func=cmd_smart_update)

    ps_del = smart_sub.add_parser("delete", help="Delete smart process item")
    ps_del.add_argument("--type-id", type=int, required=True)
    ps_del.add_argument("--id", type=int, required=True)
    ps_del.set_defaults(func=cmd_smart_delete)

    ps_stages = smart_sub.add_parser("stages", help="List smart process stages")
    ps_stages.add_argument("--type-id", type=int, required=True)
    ps_stages.set_defaults(func=cmd_smart_stages)

    # ── bp (Business Processes) ──
    p_bp = sub.add_parser("bp", help="Business Process management")
    bp_sub = p_bp.add_subparsers(dest="bp_cmd", metavar="subcommand")
    bp_sub.required = True

    pbp_list = bp_sub.add_parser("list", help="List running workflow instances")
    pbp_list.set_defaults(func=cmd_bp_list)

    pbp_start = bp_sub.add_parser("start", help="Start a business process workflow")
    pbp_start.add_argument("--template-id", type=int, required=True)
    pbp_start.add_argument("--document", required=True,
                           help="Document ID in format MODULE:ENTITY:ID (e.g. crm:CCrmLead:1)")
    pbp_start.add_argument("--param", action="append", metavar="KEY=VALUE")
    pbp_start.set_defaults(func=cmd_bp_start)

    pbp_term = bp_sub.add_parser("terminate", help="Terminate a workflow")
    pbp_term.add_argument("--workflow-id", required=True)
    pbp_term.set_defaults(func=cmd_bp_terminate)

    pbp_kill = bp_sub.add_parser("kill", help="Force kill a workflow")
    pbp_kill.add_argument("--workflow-id", required=True)
    pbp_kill.set_defaults(func=cmd_bp_kill)

    pbp_tpl = bp_sub.add_parser("templates", help="List workflow templates")
    pbp_tpl.set_defaults(func=cmd_bp_templates)

    pbp_tasks = bp_sub.add_parser("tasks", help="List pending workflow tasks")
    pbp_tasks.add_argument("--workflow-id")
    pbp_tasks.set_defaults(func=cmd_bp_tasks)

    # ── batch ──
    p_batch = sub.add_parser("batch", help="Execute multiple API methods in one request")
    p_batch.add_argument("--cmd", action="append", metavar="KEY:METHOD?PARAMS",
                         help='e.g. --cmd "u:user.get?ID=1"')
    p_batch.set_defaults(func=cmd_batch)

    # ── config ──
    p_config = sub.add_parser("config", help="Configuration management")
    config_sub = p_config.add_subparsers(dest="config_cmd", metavar="subcommand")
    config_sub.required = True

    pc_show = config_sub.add_parser("show", help="Show current configuration")
    pc_show.set_defaults(func=cmd_config_show)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    setup_logging(getattr(args, "verbose", False))

    # Inject format default for commands that don't have it
    if not hasattr(args, "format"):
        args.format = "pretty"

    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        if getattr(args, "verbose", False):
            import traceback
            traceback.print_exc()
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
