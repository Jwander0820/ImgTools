from __future__ import annotations

import argparse
import json
from typing import Any

from imgtools.service.registry import get_tool, list_tools
from imgtools.service.runner import run_tool


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="imgtools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list")

    describe_parser = subparsers.add_parser("describe")
    describe_parser.add_argument("action")

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("action")
    run_parser.add_argument("--param", action="append", default=[])
    run_parser.add_argument("--params-json", default=None)
    run_parser.add_argument("--no-manifest", action="store_true")

    ui_parser = subparsers.add_parser("ui")
    ui_parser.add_argument("--host", default="127.0.0.1")
    ui_parser.add_argument("--port", type=int, default=None)
    ui_parser.add_argument("--no-browser", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "list":
        print(json.dumps(list_tools(), ensure_ascii=False, indent=2))
    elif args.command == "describe":
        print(json.dumps(get_tool(args.action).to_dict(), ensure_ascii=False, indent=2))
    elif args.command == "run":
        params = _collect_params(args.params_json, args.param)
        result = run_tool(args.action, params, manifest=not args.no_manifest)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.command == "ui":
        from imgtools.ui.server import serve

        port = 5858 if args.port is None else args.port
        serve(args.host, port, open_browser=not args.no_browser)


def _collect_params(params_json: str | None, pairs: list[str]) -> dict[str, Any]:
    params: dict[str, Any] = {}
    if params_json:
        params.update(json.loads(params_json))
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"--param must be key=value: {pair}")
        key, value = pair.split("=", 1)
        params[key] = value
    return params
