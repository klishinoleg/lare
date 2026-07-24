from __future__ import annotations

from infrastructure.runtime.local_supervisor import (
    ContainerRuntimeSupervisor,
    ContainerSnapshot,
    EndpointCheckStatus,
    EndpointSpec,
    LocalRuntimeSupervisor,
    ProcessSnapshot,
    ProcessSpec,
    RuntimeStartCommand,
    evaluate_endpoints,
)


def test_process_status_is_running_when_all_needles_match() -> None:
    snapshots = [
        ProcessSnapshot(
            pid=33216,
            name="python.exe",
            command_line=(
                "python -m uvicorn interfaces.fast_api.main:app "
                "--host 0.0.0.0 --port 8007"
            ),
        ),
    ]
    specs = [
        ProcessSpec(
            name="backend_api",
            command_contains=("uvicorn", "interfaces.fast_api.main:app", "--port 8007"),
        ),
    ]

    status = LocalRuntimeSupervisor(specs=specs).evaluate(snapshots)

    assert status.ok is True
    assert status.components[0].running is True
    assert status.components[0].pids == (33216,)


def test_process_status_marks_missing_required_component_as_not_ok() -> None:
    specs = [
        ProcessSpec(
            name="segment_worker",
            command_contains=("faststream", "interfaces.event_broker.kafka_segment"),
        ),
    ]

    status = LocalRuntimeSupervisor(specs=specs).evaluate([])

    assert status.ok is False
    assert status.components[0].running is False
    assert status.components[0].required is True


def test_process_status_redacts_secret_like_command_values() -> None:
    snapshots = [
        ProcessSnapshot(
            pid=123,
            name="python.exe",
            command_line="python worker.py --token sk-test-secret OPENAI_API_KEY=secret-value",
        ),
    ]
    specs = [ProcessSpec(name="worker", command_contains=("worker.py",))]

    status = LocalRuntimeSupervisor(specs=specs).evaluate(snapshots)

    command_lines = status.components[0].command_lines
    assert command_lines == (
        "python worker.py --token <redacted> OPENAI_API_KEY=<redacted>",
    )


def test_default_specs_cover_lazy_reader_local_runtime() -> None:
    specs = {spec.name: spec for spec in LocalRuntimeSupervisor.default_specs()}

    assert {
        "backend_api_8007",
        "chapter_worker",
        "segment_worker",
        "finance_worker",
        "bot_worker",
        "frontend_vite_5174",
        "ngrok",
        "telegram_bot_polling",
    }.issubset(specs)
    assert "interfaces.event_broker.kafka_chapter" in specs["chapter_worker"].command_contains
    assert "interfaces.event_broker.kafka_bot" in specs["bot_worker"].command_contains
    assert specs["telegram_bot_polling"].required is False
    assert "interfaces.bot.telegram" in specs["telegram_bot_polling"].command_contains


def test_default_start_commands_cover_chapter_and_bot_workers() -> None:
    start_commands = LocalRuntimeSupervisor.default_start_commands()

    assert "chapter_worker" in start_commands
    assert ".work-start-kafka-chapter.cmd" in " ".join(start_commands["chapter_worker"].arguments)
    assert "bot_worker" in start_commands
    assert ".work-start-kafka-bot.cmd" in " ".join(start_commands["bot_worker"].arguments)


def test_repair_starts_only_missing_required_components() -> None:
    snapshots = [
        ProcessSnapshot(
            pid=33216,
            name="python.exe",
            command_line="python -m uvicorn interfaces.fast_api.main:app --port 8007",
        ),
    ]
    specs = [
        ProcessSpec(
            name="backend_api_8007",
            command_contains=("uvicorn", "interfaces.fast_api.main:app"),
        ),
        ProcessSpec(
            name="segment_worker",
            command_contains=("faststream", "interfaces.event_broker.kafka_segment"),
        ),
    ]
    start_command = RuntimeStartCommand(
        executable="cmd.exe",
        arguments=("/c", "C:/python/ddd/lare/.work-start-kafka-segment.cmd"),
        working_directory="C:/python/ddd/lare",
    )
    started: list[RuntimeStartCommand] = []

    result = LocalRuntimeSupervisor(specs=specs).repair(
        snapshots=snapshots,
        start_commands={"segment_worker": start_command},
        starter=started.append,
    )

    assert result.started_count == 1
    assert started == [start_command]
    assert result.actions[0].component_name == "segment_worker"
    assert result.actions[0].status == "started"


def test_repair_does_not_start_running_components() -> None:
    snapshots = [
        ProcessSnapshot(
            pid=32928,
            name="python.exe",
            command_line="python -m faststream run interfaces.event_broker.kafka_segment:app",
        ),
    ]
    specs = [
        ProcessSpec(
            name="segment_worker",
            command_contains=("faststream", "interfaces.event_broker.kafka_segment"),
        ),
    ]
    started: list[RuntimeStartCommand] = []

    result = LocalRuntimeSupervisor(specs=specs).repair(
        snapshots=snapshots,
        start_commands={
            "segment_worker": RuntimeStartCommand(
                executable="cmd.exe",
                arguments=("/c", "C:/python/ddd/lare/.work-start-kafka-segment.cmd"),
                working_directory="C:/python/ddd/lare",
            ),
        },
        starter=started.append,
    )

    assert result.started_count == 0
    assert result.actions == ()
    assert started == []


def test_repair_reports_missing_start_command() -> None:
    specs = [
        ProcessSpec(
            name="segment_worker",
            command_contains=("faststream", "interfaces.event_broker.kafka_segment"),
        ),
    ]

    result = LocalRuntimeSupervisor(specs=specs).repair(
        snapshots=[],
        start_commands={},
        starter=lambda command: None,
    )

    assert result.started_count == 0
    assert result.actions[0].component_name == "segment_worker"
    assert result.actions[0].status == "missing_start_command"


def test_endpoint_status_marks_required_failed_endpoint_as_not_ok() -> None:
    specs = [
        EndpointSpec(name="backend_ready", url="http://127.0.0.1:8007/ready"),
        EndpointSpec(name="frontend_public", url="https://lang-reader.ngrok.app/"),
    ]

    result = evaluate_endpoints(
        specs,
        checker=lambda spec: EndpointCheckStatus(
            name=spec.name,
            url=spec.url,
            required=spec.required,
            ok=spec.name == "frontend_public",
            status_code=200 if spec.name == "frontend_public" else 404,
            error_message=None if spec.name == "frontend_public" else "Not Found",
        ),
    )

    assert result.ok is False
    assert result.counts == {"required": 2, "ok": 1, "failed": 1}
    assert result.endpoints[0].name == "backend_ready"
    assert result.endpoints[0].status_code == 404


def test_default_endpoint_specs_cover_ready_and_public_frontend() -> None:
    specs = {spec.name: spec for spec in LocalRuntimeSupervisor.default_endpoint_specs()}

    assert {
        "backend_ready_local",
        "backend_ready_public",
        "frontend_public",
        "telegram_receiver_public",
    }.issubset(specs)
    assert specs["telegram_receiver_public"].method == "POST"
    assert specs["telegram_receiver_public"].body == "{}"


def test_container_status_covers_linux_runtime_and_windows_ngrok() -> None:
    containers = [
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
    ]
    processes = [
        ProcessSnapshot(
            pid=39792,
            name="ngrok.exe",
            command_line="ngrok.exe start --all --config ngrok.yml",
        )
    ]

    status = ContainerRuntimeSupervisor.default().evaluate(
        containers=containers,
        processes=processes,
    )

    assert status.ok is True
    assert status.counts == {"required": 11, "running": 11, "missing": 0}
    components = {component.name: component for component in status.components}
    assert components["api"].running is True
    assert components["ngrok"].component_type == "process"
    assert components["ngrok"].pids == (39792,)


def test_container_status_marks_missing_worker_as_not_ok() -> None:
    containers = [
        ContainerSnapshot(name="lare_codex_api", status="Up 10 minutes"),
    ]

    status = ContainerRuntimeSupervisor.default().evaluate(
        containers=containers,
        processes=[],
    )

    assert status.ok is False
    assert status.counts["missing"] > 0
    components = {component.name: component for component in status.components}
    assert components["segment_worker"].running is False
    assert components["ngrok"].running is False


def test_container_repair_starts_compose_stack_once_when_any_required_missing() -> None:
    started: list[RuntimeStartCommand] = []
    processes = [
        ProcessSnapshot(
            pid=39792,
            name="ngrok.exe",
            command_line="ngrok.exe start --all --config ngrok.yml",
        )
    ]

    result = ContainerRuntimeSupervisor.default().repair(
        containers=[],
        processes=processes,
        starter=started.append,
    )

    assert result.started_count == 1
    assert result.actions[0].component_name == "container_stack"
    assert result.actions[0].status == "started"
    assert "docker compose" in " ".join(started[0].arguments)
    assert "codex_api" in " ".join(started[0].arguments)


def test_container_repair_starts_ngrok_when_only_ngrok_is_missing() -> None:
    containers = [
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
    ]
    started: list[RuntimeStartCommand] = []

    result = ContainerRuntimeSupervisor.default().repair(
        containers=containers,
        processes=[],
        starter=started.append,
    )

    assert result.started_count == 1
    assert result.actions[0].component_name == "ngrok"
    assert result.actions[0].status == "started"
    assert "ngrok.exe" in " ".join(started[0].arguments)
    assert "docker compose" not in " ".join(started[0].arguments)


def test_container_repair_starts_compose_and_ngrok_when_both_are_missing() -> None:
    started: list[RuntimeStartCommand] = []

    result = ContainerRuntimeSupervisor.default().repair(
        containers=[],
        processes=[],
        starter=started.append,
    )

    assert result.started_count == 2
    assert [action.component_name for action in result.actions] == [
        "container_stack",
        "ngrok",
    ]
    assert "docker compose" in " ".join(started[0].arguments)
    assert "ngrok.exe" in " ".join(started[1].arguments)
