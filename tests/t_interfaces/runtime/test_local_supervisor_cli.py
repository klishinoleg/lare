from __future__ import annotations

import json
from io import StringIO

from infrastructure.runtime.local_supervisor import (
    ContainerSnapshot,
    EndpointCheckStatus,
    ProcessSnapshot,
    RuntimeStartCommand,
)


def test_runtime_status_cli_outputs_json_for_current_components() -> None:
    from interfaces.runtime import local_supervisor_cli

    stdout = StringIO()
    exit_code = local_supervisor_cli.run(
        ["status"],
        stdout=stdout,
        process_provider=lambda: [
            ProcessSnapshot(
                pid=33216,
                name="python.exe",
                command_line=(
                    "python -m uvicorn interfaces.fast_api.main:app "
                    "--host 0.0.0.0 --port 8007"
                ),
            ),
            ProcessSnapshot(
                pid=32928,
                name="python.exe",
                command_line=(
                    "python -m faststream run "
                    "interfaces.event_broker.kafka_chapter:app"
                ),
            ),
            ProcessSnapshot(
                pid=32929,
                name="python.exe",
                command_line=(
                    "python -m faststream run "
                    "interfaces.event_broker.kafka_segment:app"
                ),
            ),
            ProcessSnapshot(
                pid=25124,
                name="python.exe",
                command_line=(
                    "python -m faststream run "
                    "interfaces.event_broker.kafka_finance:app"
                ),
            ),
            ProcessSnapshot(
                pid=25125,
                name="python.exe",
                command_line=(
                    "python -m faststream run "
                    "interfaces.event_broker.kafka_bot:app"
                ),
            ),
            ProcessSnapshot(
                pid=11208,
                name="node.exe",
                command_line="vite --host 0.0.0.0 --port 5174",
            ),
            ProcessSnapshot(
                pid=39792,
                name="ngrok.exe",
                command_line="ngrok.exe start --all --config ngrok.yml",
            ),
        ],
    )
    payload = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["counts"] == {"required": 7, "running": 7, "missing": 0}
    optional = {
        item["name"]: item
        for item in payload["components"]
        if not item["required"]
    }
    assert "telegram_bot_polling" in optional
    assert optional["telegram_bot_polling"]["running"] is False


def test_runtime_status_cli_can_fail_when_required_process_missing() -> None:
    from interfaces.runtime import local_supervisor_cli

    stdout = StringIO()
    exit_code = local_supervisor_cli.run(
        ["status", "--fail-on-missing"],
        stdout=stdout,
        process_provider=lambda: [],
    )
    payload = json.loads(stdout.getvalue())

    assert exit_code == 2
    assert payload["ok"] is False
    assert payload["counts"]["missing"] == 7


def test_runtime_repair_cli_does_not_start_when_everything_is_running() -> None:
    from interfaces.runtime import local_supervisor_cli

    stdout = StringIO()
    started: list[RuntimeStartCommand] = []
    exit_code = local_supervisor_cli.run(
        ["repair"],
        stdout=stdout,
        process_provider=lambda: [
            ProcessSnapshot(
                pid=33216,
                name="python.exe",
                command_line=(
                    "python -m uvicorn interfaces.fast_api.main:app "
                    "--host 0.0.0.0 --port 8007"
                ),
            ),
            ProcessSnapshot(
                pid=32928,
                name="python.exe",
                command_line=(
                    "python -m faststream run "
                    "interfaces.event_broker.kafka_chapter:app"
                ),
            ),
            ProcessSnapshot(
                pid=32929,
                name="python.exe",
                command_line=(
                    "python -m faststream run "
                    "interfaces.event_broker.kafka_segment:app"
                ),
            ),
            ProcessSnapshot(
                pid=25124,
                name="python.exe",
                command_line=(
                    "python -m faststream run "
                    "interfaces.event_broker.kafka_finance:app"
                ),
            ),
            ProcessSnapshot(
                pid=25125,
                name="python.exe",
                command_line=(
                    "python -m faststream run "
                    "interfaces.event_broker.kafka_bot:app"
                ),
            ),
            ProcessSnapshot(
                pid=11208,
                name="node.exe",
                command_line="vite --host 0.0.0.0 --port 5174",
            ),
            ProcessSnapshot(
                pid=39792,
                name="ngrok.exe",
                command_line="ngrok.exe start --all --config ngrok.yml",
            ),
        ],
        starter=started.append,
    )
    payload = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert started == []
    assert payload["repair"]["started_count"] == 0
    assert payload["repair"]["actions"] == []


def test_runtime_repair_cli_starts_missing_finance_worker() -> None:
    from interfaces.runtime import local_supervisor_cli

    stdout = StringIO()
    started: list[RuntimeStartCommand] = []
    exit_code = local_supervisor_cli.run(
        ["repair"],
        stdout=stdout,
        process_provider=lambda: [
            ProcessSnapshot(
                pid=33216,
                name="python.exe",
                command_line=(
                    "python -m uvicorn interfaces.fast_api.main:app "
                    "--host 0.0.0.0 --port 8007"
                ),
            ),
            ProcessSnapshot(
                pid=32928,
                name="python.exe",
                command_line=(
                    "python -m faststream run "
                    "interfaces.event_broker.kafka_chapter:app"
                ),
            ),
            ProcessSnapshot(
                pid=32929,
                name="python.exe",
                command_line=(
                    "python -m faststream run "
                    "interfaces.event_broker.kafka_segment:app"
                ),
            ),
            ProcessSnapshot(
                pid=25125,
                name="python.exe",
                command_line=(
                    "python -m faststream run "
                    "interfaces.event_broker.kafka_bot:app"
                ),
            ),
            ProcessSnapshot(
                pid=11208,
                name="node.exe",
                command_line="vite --host 0.0.0.0 --port 5174",
            ),
            ProcessSnapshot(
                pid=39792,
                name="ngrok.exe",
                command_line="ngrok.exe start --all --config ngrok.yml",
            ),
        ],
        starter=started.append,
    )
    payload = json.loads(stdout.getvalue())

    assert exit_code == 1
    assert len(started) == 1
    assert ".work-start-kafka-finance.cmd" in " ".join(started[0].arguments)
    assert payload["repair"]["started_count"] == 1
    assert payload["repair"]["actions"][0]["component_name"] == "finance_worker"
    assert payload["repair"]["actions"][0]["status"] == "started"


def test_runtime_status_cli_can_check_http_endpoints() -> None:
    from interfaces.runtime import local_supervisor_cli

    stdout = StringIO()
    exit_code = local_supervisor_cli.run(
        ["status", "--check-endpoints", "--fail-on-missing"],
        stdout=stdout,
        process_provider=lambda: [
            ProcessSnapshot(
                pid=33216,
                name="python.exe",
                command_line=(
                    "python -m uvicorn interfaces.fast_api.main:app "
                    "--host 0.0.0.0 --port 8007"
                ),
            ),
            ProcessSnapshot(
                pid=32928,
                name="python.exe",
                command_line=(
                    "python -m faststream run "
                    "interfaces.event_broker.kafka_chapter:app"
                ),
            ),
            ProcessSnapshot(
                pid=32929,
                name="python.exe",
                command_line=(
                    "python -m faststream run "
                    "interfaces.event_broker.kafka_segment:app"
                ),
            ),
            ProcessSnapshot(
                pid=25124,
                name="python.exe",
                command_line=(
                    "python -m faststream run "
                    "interfaces.event_broker.kafka_finance:app"
                ),
            ),
            ProcessSnapshot(
                pid=25125,
                name="python.exe",
                command_line=(
                    "python -m faststream run "
                    "interfaces.event_broker.kafka_bot:app"
                ),
            ),
            ProcessSnapshot(
                pid=11208,
                name="node.exe",
                command_line="vite --host 0.0.0.0 --port 5174",
            ),
            ProcessSnapshot(
                pid=39792,
                name="ngrok.exe",
                command_line="ngrok.exe start --all --config ngrok.yml",
            ),
        ],
        endpoint_checker=lambda spec: EndpointCheckStatus(
            name=spec.name,
            url=spec.url,
            required=spec.required,
            ok=True,
            status_code=200,
            error_message=None,
        ),
    )
    payload = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["endpoints"]["counts"] == {"required": 4, "ok": 4, "failed": 0}


def test_runtime_status_cli_supports_container_profile() -> None:
    from interfaces.runtime import local_supervisor_cli

    stdout = StringIO()
    exit_code = local_supervisor_cli.run(
        ["status", "--profile", "containers"],
        stdout=stdout,
        process_provider=lambda: [
            ProcessSnapshot(
                pid=39792,
                name="ngrok.exe",
                command_line="ngrok.exe start --all --config ngrok.yml",
            )
        ],
        container_provider=lambda: [
            ContainerSnapshot(name="lare_codex_api", status="Up 10 minutes"),
            ContainerSnapshot(name="lare_codex_kafka_segment", status="Up 10 minutes"),
            ContainerSnapshot(name="lare_codex_kafka_chapter", status="Up 10 minutes"),
            ContainerSnapshot(name="lare_codex_kafka_finance", status="Up 10 minutes"),
            ContainerSnapshot(name="lare_codex_kafka_bot", status="Up 10 minutes"),
            ContainerSnapshot(name="lare_codex_frontend", status="Up 10 minutes"),
            ContainerSnapshot(name="lare_test_redis", status="Up 10 minutes"),
            ContainerSnapshot(name="lare_test_zookeeper", status="Up 10 minutes"),
            ContainerSnapshot(name="lare_test_kafka", status="Up 10 minutes"),
            ContainerSnapshot(name="lare_test_kafka_ui", status="Up 10 minutes"),
        ],
    )
    payload = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert payload["profile"] == "containers"
    assert payload["ok"] is True
    assert payload["counts"] == {"required": 11, "running": 11, "missing": 0}


def test_runtime_repair_cli_supports_container_profile() -> None:
    from interfaces.runtime import local_supervisor_cli

    stdout = StringIO()
    started: list[RuntimeStartCommand] = []
    exit_code = local_supervisor_cli.run(
        ["repair", "--profile", "containers"],
        stdout=stdout,
        process_provider=lambda: [],
        container_provider=lambda: [],
        starter=started.append,
    )
    payload = json.loads(stdout.getvalue())

    assert exit_code == 1
    assert len(started) == 2
    assert payload["profile"] == "containers"
    assert payload["repair"]["started_count"] == 2
    assert payload["repair"]["actions"][0]["component_name"] == "container_stack"
    assert payload["repair"]["actions"][1]["component_name"] == "ngrok"


def test_runtime_repair_cli_starts_ngrok_for_container_profile_when_only_edge_missing() -> None:
    from interfaces.runtime import local_supervisor_cli

    stdout = StringIO()
    started: list[RuntimeStartCommand] = []
    exit_code = local_supervisor_cli.run(
        ["repair", "--profile", "containers"],
        stdout=stdout,
        process_provider=lambda: [],
        container_provider=lambda: [
            ContainerSnapshot(name="lare_codex_api", status="Up 10 minutes"),
            ContainerSnapshot(name="lare_codex_kafka_segment", status="Up 10 minutes"),
            ContainerSnapshot(name="lare_codex_kafka_chapter", status="Up 10 minutes"),
            ContainerSnapshot(name="lare_codex_kafka_finance", status="Up 10 minutes"),
            ContainerSnapshot(name="lare_codex_kafka_bot", status="Up 10 minutes"),
            ContainerSnapshot(name="lare_codex_frontend", status="Up 10 minutes"),
            ContainerSnapshot(name="lare_test_redis", status="Up 10 minutes"),
            ContainerSnapshot(name="lare_test_zookeeper", status="Up 10 minutes"),
            ContainerSnapshot(name="lare_test_kafka", status="Up 10 minutes"),
            ContainerSnapshot(name="lare_test_kafka_ui", status="Up 10 minutes"),
        ],
        starter=started.append,
    )
    payload = json.loads(stdout.getvalue())

    assert exit_code == 1
    assert len(started) == 1
    assert payload["repair"]["started_count"] == 1
    assert payload["repair"]["actions"][0]["component_name"] == "ngrok"
    assert "ngrok.exe" in " ".join(started[0].arguments)
