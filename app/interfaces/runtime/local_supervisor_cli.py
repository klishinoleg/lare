from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from typing import TextIO

from infrastructure.runtime.local_supervisor import (
    ContainerRuntimeSupervisor,
    ContainerSnapshot,
    EndpointChecker,
    LocalRuntimeSupervisor,
    ProcessSnapshot,
    RuntimeStarter,
    check_runtime_endpoint,
    collect_container_snapshots,
    collect_process_snapshots,
    evaluate_endpoints,
    start_runtime_component,
)


ProcessProvider = Callable[[], tuple[ProcessSnapshot, ...] | list[ProcessSnapshot]]
ContainerProvider = Callable[[], tuple[ContainerSnapshot, ...] | list[ContainerSnapshot]]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect Lazy Reader local runtime processes."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    status_parser = subparsers.add_parser(
        "status",
        help="Print local backend/frontend worker process status as JSON.",
    )
    status_parser.add_argument(
        "--fail-on-missing",
        action="store_true",
        help="Exit with code 2 when a required runtime component is missing.",
    )
    status_parser.add_argument(
        "--check-endpoints",
        action="store_true",
        help="Also check local/public HTTP readiness endpoints.",
    )
    status_parser.add_argument(
        "--profile",
        choices=("processes", "containers"),
        default="processes",
        help="Runtime profile to inspect. Use containers for the WSL Docker contour.",
    )
    repair_parser = subparsers.add_parser(
        "repair",
        help="Start missing local runtime components with configured commands.",
    )
    repair_parser.add_argument(
        "--profile",
        choices=("processes", "containers"),
        default="processes",
        help="Runtime profile to repair. Use containers for the WSL Docker contour.",
    )
    return parser


def run(
    argv: list[str] | None = None,
    stdout: TextIO = sys.stdout,
    process_provider: ProcessProvider = collect_process_snapshots,
    container_provider: ContainerProvider = collect_container_snapshots,
    starter: RuntimeStarter = start_runtime_component,
    endpoint_checker: EndpointChecker = check_runtime_endpoint,
) -> int:
    args = _parser().parse_args(argv)

    if args.command == "status":
        if args.profile == "containers":
            container_supervisor = ContainerRuntimeSupervisor.default()
            status = container_supervisor.evaluate(
                containers=container_provider(),
                processes=process_provider(),
            )
        else:
            supervisor = LocalRuntimeSupervisor(
                specs=LocalRuntimeSupervisor.default_specs(),
            )
            status = supervisor.evaluate(process_provider())
        payload = {"profile": args.profile, **status.to_dict()}
        if args.check_endpoints:
            endpoint_status = evaluate_endpoints(
                LocalRuntimeSupervisor.default_endpoint_specs(),
                endpoint_checker,
            )
            payload["endpoints"] = endpoint_status.to_dict()
            payload["ok"] = status.ok and endpoint_status.ok

        stdout.write(json.dumps(payload, ensure_ascii=False))
        stdout.write("\n")
        if args.fail_on_missing and not payload["ok"]:
            return 2
        return 0

    if args.command == "repair":
        if args.profile == "containers":
            container_supervisor = ContainerRuntimeSupervisor.default()
            repair = container_supervisor.repair(
                containers=container_provider(),
                processes=process_provider(),
                starter=starter,
            )
        else:
            supervisor = LocalRuntimeSupervisor(
                specs=LocalRuntimeSupervisor.default_specs(),
            )
            repair = supervisor.repair(
                snapshots=process_provider(),
                start_commands=LocalRuntimeSupervisor.default_start_commands(),
                starter=starter,
            )
        stdout.write(
            json.dumps(
                {
                    "profile": args.profile,
                    "ok": repair.before.ok,
                    "counts": repair.before.counts,
                    "repair": repair.to_dict(),
                },
                ensure_ascii=False,
            )
        )
        stdout.write("\n")
        if repair.before.ok:
            return 0
        if repair.missing_start_command_count:
            return 2
        return 1

    raise ValueError(f"Unsupported command: {args.command}")


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
