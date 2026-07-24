from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ProcessSnapshot:
    pid: int
    name: str
    command_line: str


@dataclass(frozen=True)
class ProcessSpec:
    name: str
    command_contains: tuple[str, ...]
    required: bool = True


@dataclass(frozen=True)
class ContainerSnapshot:
    name: str
    status: str


@dataclass(frozen=True)
class ContainerSpec:
    name: str
    container_name: str
    required: bool = True


@dataclass(frozen=True)
class ProcessComponentStatus:
    name: str
    required: bool
    running: bool
    pids: tuple[int, ...]
    command_lines: tuple[str, ...]


@dataclass(frozen=True)
class RuntimeComponentStatus:
    name: str
    component_type: str
    required: bool
    running: bool
    container_name: str | None = None
    container_status: str | None = None
    pids: tuple[int, ...] = ()
    command_lines: tuple[str, ...] = ()


@dataclass(frozen=True)
class RuntimeStartCommand:
    executable: str
    arguments: tuple[str, ...]
    working_directory: str


@dataclass(frozen=True)
class RuntimeRepairAction:
    component_name: str
    status: str
    command: RuntimeStartCommand | None


@dataclass(frozen=True)
class EndpointSpec:
    name: str
    url: str
    expected_status: int = 200
    required: bool = True
    method: str = "GET"
    body: str | None = None
    content_type: str | None = None


@dataclass(frozen=True)
class EndpointCheckStatus:
    name: str
    url: str
    required: bool
    ok: bool
    status_code: int | None
    error_message: str | None


@dataclass(frozen=True)
class RuntimeStatus:
    ok: bool
    components: tuple[ProcessComponentStatus, ...]

    @property
    def counts(self) -> dict[str, int]:
        required_components = [item for item in self.components if item.required]
        running = sum(1 for item in required_components if item.running)
        missing = len(required_components) - running
        return {
            "required": len(required_components),
            "running": running,
            "missing": missing,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "counts": self.counts,
            "components": [asdict(component) for component in self.components],
        }


@dataclass(frozen=True)
class ContainerRuntimeStatus:
    ok: bool
    components: tuple[RuntimeComponentStatus, ...]

    @property
    def counts(self) -> dict[str, int]:
        required_components = [item for item in self.components if item.required]
        running = sum(1 for item in required_components if item.running)
        missing = len(required_components) - running
        return {
            "required": len(required_components),
            "running": running,
            "missing": missing,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "counts": self.counts,
            "components": [asdict(component) for component in self.components],
        }


@dataclass(frozen=True)
class RuntimeRepairResult:
    before: RuntimeStatus
    actions: tuple[RuntimeRepairAction, ...]

    @property
    def started_count(self) -> int:
        return sum(1 for action in self.actions if action.status == "started")

    @property
    def missing_start_command_count(self) -> int:
        return sum(
            1 for action in self.actions if action.status == "missing_start_command"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "before": self.before.to_dict(),
            "started_count": self.started_count,
            "missing_start_command_count": self.missing_start_command_count,
            "actions": [asdict(action) for action in self.actions],
        }


@dataclass(frozen=True)
class ContainerRuntimeRepairResult:
    before: ContainerRuntimeStatus
    actions: tuple[RuntimeRepairAction, ...]

    @property
    def started_count(self) -> int:
        return sum(1 for action in self.actions if action.status == "started")

    @property
    def missing_start_command_count(self) -> int:
        return sum(
            1 for action in self.actions if action.status == "missing_start_command"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "before": self.before.to_dict(),
            "started_count": self.started_count,
            "missing_start_command_count": self.missing_start_command_count,
            "actions": [asdict(action) for action in self.actions],
        }


RuntimeStarter = Callable[[RuntimeStartCommand], object]
EndpointChecker = Callable[[EndpointSpec], EndpointCheckStatus]


@dataclass(frozen=True)
class EndpointCheckResult:
    ok: bool
    endpoints: tuple[EndpointCheckStatus, ...]

    @property
    def counts(self) -> dict[str, int]:
        required_endpoints = [item for item in self.endpoints if item.required]
        ok_count = sum(1 for item in required_endpoints if item.ok)
        failed = len(required_endpoints) - ok_count
        return {
            "required": len(required_endpoints),
            "ok": ok_count,
            "failed": failed,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "counts": self.counts,
            "endpoints": [asdict(endpoint) for endpoint in self.endpoints],
        }


class LocalRuntimeSupervisor:
    def __init__(self, specs: Sequence[ProcessSpec]) -> None:
        self._specs = tuple(specs)

    @staticmethod
    def default_specs() -> tuple[ProcessSpec, ...]:
        return (
            ProcessSpec(
                name="backend_api_8007",
                command_contains=(
                    "uvicorn",
                    "interfaces.fast_api.main:app",
                    "--port 8007",
                ),
            ),
            ProcessSpec(
                name="segment_worker",
                command_contains=(
                    "faststream",
                    "interfaces.event_broker.kafka_segment",
                ),
            ),
            ProcessSpec(
                name="chapter_worker",
                command_contains=(
                    "faststream",
                    "interfaces.event_broker.kafka_chapter",
                ),
            ),
            ProcessSpec(
                name="finance_worker",
                command_contains=(
                    "faststream",
                    "interfaces.event_broker.kafka_finance",
                ),
            ),
            ProcessSpec(
                name="bot_worker",
                command_contains=(
                    "faststream",
                    "interfaces.event_broker.kafka_bot",
                ),
            ),
            ProcessSpec(
                name="frontend_vite_5174",
                command_contains=(
                    "vite",
                    "--port 5174",
                ),
            ),
            ProcessSpec(
                name="ngrok",
                command_contains=(
                    "ngrok",
                    "ngrok.yml",
                ),
            ),
            ProcessSpec(
                name="telegram_bot_polling",
                command_contains=(
                    "interfaces.bot.telegram",
                ),
                required=False,
            ),
        )

    @staticmethod
    def default_start_commands() -> dict[str, RuntimeStartCommand]:
        return {
            "backend_api_8007": RuntimeStartCommand(
                executable="cmd.exe",
                arguments=("/c", "C:/python/ddd/lare/.work-start-api-8007-kafka.cmd"),
                working_directory="C:/python/ddd/lare",
            ),
            "segment_worker": RuntimeStartCommand(
                executable="cmd.exe",
                arguments=("/c", "C:/python/ddd/lare/.work-start-kafka-segment.cmd"),
                working_directory="C:/python/ddd/lare",
            ),
            "chapter_worker": RuntimeStartCommand(
                executable="cmd.exe",
                arguments=("/c", "C:/python/ddd/lare/.work-start-kafka-chapter.cmd"),
                working_directory="C:/python/ddd/lare",
            ),
            "finance_worker": RuntimeStartCommand(
                executable="cmd.exe",
                arguments=("/c", "C:/python/ddd/lare/.work-start-kafka-finance.cmd"),
                working_directory="C:/python/ddd/lare",
            ),
            "bot_worker": RuntimeStartCommand(
                executable="cmd.exe",
                arguments=("/c", "C:/python/ddd/lare/.work-start-kafka-bot.cmd"),
                working_directory="C:/python/ddd/lare",
            ),
            "frontend_vite_5174": RuntimeStartCommand(
                executable="cmd.exe",
                arguments=("/c", "C:/apps/lang_reader/.work-start-vite-5174-kafka.cmd"),
                working_directory="C:/apps/lang_reader",
            ),
            "ngrok": RuntimeStartCommand(
                executable="cmd.exe",
                arguments=(
                    "/c",
                    (
                        "C:/Users/klish/AppData/Local/ngrok/ngrok.exe "
                        "start --all --config "
                        "C:/Users/klish/AppData/Local/ngrok/ngrok.yml "
                        "> C:/python/ddd/ai/.work/ngrok-local.log "
                        "2> C:/python/ddd/ai/.work/ngrok-local.err.log"
                    ),
                ),
                working_directory="C:/Users/klish/AppData/Local/ngrok",
            ),
            "telegram_bot_polling": RuntimeStartCommand(
                executable="cmd.exe",
                arguments=("/c", "C:/python/ddd/lare/.work-start-telegram-bot.cmd"),
                working_directory="C:/python/ddd/lare",
            ),
        }

    @staticmethod
    def default_endpoint_specs() -> tuple[EndpointSpec, ...]:
        return (
            EndpointSpec(
                name="backend_ready_local",
                url="http://127.0.0.1:8007/ready",
            ),
            EndpointSpec(
                name="backend_ready_public",
                url="https://lang-reader-server.ngrok.app/ready",
            ),
            EndpointSpec(
                name="frontend_public",
                url="https://lang-reader.ngrok.app/",
            ),
            EndpointSpec(
                name="telegram_receiver_public",
                url="https://lang-reader-server.ngrok.app/api/v1/telegram/update/",
                method="POST",
                body="{}",
                content_type="application/json",
            ),
        )

    def evaluate(self, snapshots: Sequence[ProcessSnapshot]) -> RuntimeStatus:
        components = tuple(
            self._evaluate_component(spec=spec, snapshots=snapshots)
            for spec in self._specs
        )
        ok = all(component.running for component in components if component.required)
        return RuntimeStatus(ok=ok, components=components)

    def repair(
        self,
        *,
        snapshots: Sequence[ProcessSnapshot],
        start_commands: Mapping[str, RuntimeStartCommand],
        starter: RuntimeStarter,
    ) -> RuntimeRepairResult:
        before = self.evaluate(snapshots)
        actions: list[RuntimeRepairAction] = []

        for component in before.components:
            if not component.required or component.running:
                continue

            start_command = start_commands.get(component.name)
            if start_command is None:
                actions.append(
                    RuntimeRepairAction(
                        component_name=component.name,
                        status="missing_start_command",
                        command=None,
                    )
                )
                continue

            starter(start_command)
            actions.append(
                RuntimeRepairAction(
                    component_name=component.name,
                    status="started",
                    command=start_command,
                )
            )

        return RuntimeRepairResult(before=before, actions=tuple(actions))

    def _evaluate_component(
        self,
        *,
        spec: ProcessSpec,
        snapshots: Sequence[ProcessSnapshot],
    ) -> ProcessComponentStatus:
        matches = tuple(
            snapshot
            for snapshot in snapshots
            if _command_matches(snapshot.command_line, spec.command_contains)
        )
        return ProcessComponentStatus(
            name=spec.name,
            required=spec.required,
            running=bool(matches),
            pids=tuple(snapshot.pid for snapshot in matches),
            command_lines=tuple(
                _redact_command_line(snapshot.command_line) for snapshot in matches
            ),
        )


class ContainerRuntimeSupervisor:
    def __init__(
        self,
        *,
        container_specs: Sequence[ContainerSpec],
        process_specs: Sequence[ProcessSpec],
        container_start_command: RuntimeStartCommand,
        process_start_commands: Mapping[str, RuntimeStartCommand],
    ) -> None:
        self._container_specs = tuple(container_specs)
        self._process_specs = tuple(process_specs)
        self._container_start_command = container_start_command
        self._process_start_commands = dict(process_start_commands)

    @classmethod
    def default(cls) -> ContainerRuntimeSupervisor:
        return cls(
            container_specs=cls.default_container_specs(),
            process_specs=cls.default_process_specs(),
            container_start_command=cls.default_container_start_command(),
            process_start_commands=cls.default_process_start_commands(),
        )

    @staticmethod
    def default_container_specs() -> tuple[ContainerSpec, ...]:
        return (
            ContainerSpec(name="api", container_name="lare_codex_api"),
            ContainerSpec(
                name="segment_worker",
                container_name="lare_codex_kafka_segment",
            ),
            ContainerSpec(
                name="chapter_worker",
                container_name="lare_codex_kafka_chapter",
            ),
            ContainerSpec(
                name="finance_worker",
                container_name="lare_codex_kafka_finance",
            ),
            ContainerSpec(name="bot_worker", container_name="lare_codex_kafka_bot"),
            ContainerSpec(name="frontend", container_name="lare_codex_frontend"),
            ContainerSpec(name="redis", container_name="lare_test_redis"),
            ContainerSpec(name="zookeeper", container_name="lare_test_zookeeper"),
            ContainerSpec(name="kafka", container_name="lare_test_kafka"),
            ContainerSpec(name="kafka_ui", container_name="lare_test_kafka_ui"),
        )

    @staticmethod
    def default_process_specs() -> tuple[ProcessSpec, ...]:
        return (
            ProcessSpec(
                name="ngrok",
                command_contains=("ngrok", "ngrok.yml"),
            ),
        )

    @staticmethod
    def default_container_start_command() -> RuntimeStartCommand:
        compose_command = (
            "cd /mnt/c/python/ddd/lare && "
            "docker compose "
            "-f tests_env/docker-compose.yml "
            "-f tests_env/docker-compose.codex-local.yml "
            "up -d --build "
            "redis zookeeper kafka kafka-topic-init kafka_ui "
            "codex_api codex_kafka_segment codex_kafka_chapter "
            "codex_kafka_finance codex_kafka_bot codex_frontend"
        )
        return RuntimeStartCommand(
            executable="wsl",
            arguments=(
                "-d",
                "Ubuntu",
                "-u",
                "root",
                "--",
                "sh",
                "-lc",
                compose_command,
            ),
            working_directory="C:/python/ddd/lare",
        )

    @staticmethod
    def default_process_start_commands() -> dict[str, RuntimeStartCommand]:
        return {
            "ngrok": RuntimeStartCommand(
                executable="cmd.exe",
                arguments=(
                    "/c",
                    (
                        "C:/Users/klish/AppData/Local/ngrok/ngrok.exe "
                        "start --all --config "
                        "C:/Users/klish/AppData/Local/ngrok/ngrok.yml "
                        "> C:/python/ddd/ai/.work/ngrok-local.log "
                        "2> C:/python/ddd/ai/.work/ngrok-local.err.log"
                    ),
                ),
                working_directory="C:/Users/klish/AppData/Local/ngrok",
            ),
        }

    def evaluate(
        self,
        *,
        containers: Sequence[ContainerSnapshot],
        processes: Sequence[ProcessSnapshot],
    ) -> ContainerRuntimeStatus:
        components = [
            self._evaluate_container_component(spec=spec, containers=containers)
            for spec in self._container_specs
        ]
        components.extend(
            self._evaluate_process_component(spec=spec, processes=processes)
            for spec in self._process_specs
        )
        ok = all(component.running for component in components if component.required)
        return ContainerRuntimeStatus(ok=ok, components=tuple(components))

    def repair(
        self,
        *,
        containers: Sequence[ContainerSnapshot],
        processes: Sequence[ProcessSnapshot],
        starter: RuntimeStarter,
    ) -> ContainerRuntimeRepairResult:
        before = self.evaluate(containers=containers, processes=processes)
        if before.ok:
            return ContainerRuntimeRepairResult(before=before, actions=())

        actions: list[RuntimeRepairAction] = []
        container_missing = any(
            component.required
            and not component.running
            and component.component_type == "container"
            for component in before.components
        )
        if container_missing:
            starter(self._container_start_command)
            actions.append(
                RuntimeRepairAction(
                    component_name="container_stack",
                    status="started",
                    command=self._container_start_command,
                )
            )

        for component in before.components:
            if (
                not component.required
                or component.running
                or component.component_type != "process"
            ):
                continue
            start_command = self._process_start_commands.get(component.name)
            if start_command is None:
                actions.append(
                    RuntimeRepairAction(
                        component_name=component.name,
                        status="missing_start_command",
                        command=None,
                    )
                )
                continue
            starter(start_command)
            actions.append(
                RuntimeRepairAction(
                    component_name=component.name,
                    status="started",
                    command=start_command,
                )
            )

        return ContainerRuntimeRepairResult(
            before=before,
            actions=tuple(actions),
        )

    def _evaluate_container_component(
        self,
        *,
        spec: ContainerSpec,
        containers: Sequence[ContainerSnapshot],
    ) -> RuntimeComponentStatus:
        container = next(
            (item for item in containers if item.name == spec.container_name),
            None,
        )
        return RuntimeComponentStatus(
            name=spec.name,
            component_type="container",
            required=spec.required,
            running=container is not None and container.status.startswith("Up"),
            container_name=spec.container_name,
            container_status=container.status if container else None,
        )

    def _evaluate_process_component(
        self,
        *,
        spec: ProcessSpec,
        processes: Sequence[ProcessSnapshot],
    ) -> RuntimeComponentStatus:
        matches = tuple(
            process
            for process in processes
            if _command_matches(process.command_line, spec.command_contains)
        )
        return RuntimeComponentStatus(
            name=spec.name,
            component_type="process",
            required=spec.required,
            running=bool(matches),
            pids=tuple(process.pid for process in matches),
            command_lines=tuple(
                _redact_command_line(process.command_line) for process in matches
            ),
        )


def collect_process_snapshots(timeout_seconds: int = 15) -> tuple[ProcessSnapshot, ...]:
    script = (
        "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
        "$OutputEncoding=[System.Text.Encoding]::UTF8; "
        "Get-CimInstance Win32_Process | "
        "Select-Object ProcessId,Name,CommandLine | ConvertTo-Json -Depth 3"
    )
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True,
        check=True,
        encoding="utf-8",
        text=True,
        timeout=timeout_seconds,
    )
    raw_output = completed.stdout.strip()
    if not raw_output:
        return ()

    raw_items = json.loads(raw_output)
    if isinstance(raw_items, dict):
        raw_items = [raw_items]

    return tuple(_snapshot_from_powershell_item(item) for item in raw_items)


def collect_container_snapshots(timeout_seconds: int = 15) -> tuple[ContainerSnapshot, ...]:
    completed = subprocess.run(
        [
            "wsl",
            "-d",
            "Ubuntu",
            "-u",
            "root",
            "--",
            "docker",
            "ps",
            "--format",
            "{{json .}}",
        ],
        capture_output=True,
        check=True,
        encoding="utf-8",
        text=True,
        timeout=timeout_seconds,
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    return tuple(_snapshot_from_docker_json_line(line) for line in lines)


def start_runtime_component(command: RuntimeStartCommand) -> subprocess.Popen[bytes]:
    startupinfo = None
    creationflags = 0
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        creationflags |= getattr(subprocess, "DETACHED_PROCESS", 0)

    return subprocess.Popen(
        [command.executable, *command.arguments],
        cwd=command.working_directory,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        startupinfo=startupinfo,
        creationflags=creationflags,
    )


def evaluate_endpoints(
    specs: Sequence[EndpointSpec],
    checker: EndpointChecker,
) -> EndpointCheckResult:
    endpoints = tuple(checker(spec) for spec in specs)
    ok = all(endpoint.ok for endpoint in endpoints if endpoint.required)
    return EndpointCheckResult(ok=ok, endpoints=endpoints)


def check_runtime_endpoint(
    spec: EndpointSpec,
    timeout_seconds: int = 10,
) -> EndpointCheckStatus:
    headers = {"ngrok-skip-browser-warning": "true"}
    body = None
    if spec.body is not None:
        body = spec.body.encode("utf-8")
        headers["Content-Type"] = spec.content_type or "application/octet-stream"
    request = urllib.request.Request(
        spec.url,
        data=body,
        headers=headers,
        method=spec.method.upper(),
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            status_code = int(response.status)
    except urllib.error.HTTPError as exc:
        return EndpointCheckStatus(
            name=spec.name,
            url=spec.url,
            required=spec.required,
            ok=False,
            status_code=int(exc.code),
            error_message=str(exc.reason),
        )
    except (OSError, TimeoutError, urllib.error.URLError) as exc:
        return EndpointCheckStatus(
            name=spec.name,
            url=spec.url,
            required=spec.required,
            ok=False,
            status_code=None,
            error_message=str(exc),
        )

    return EndpointCheckStatus(
        name=spec.name,
        url=spec.url,
        required=spec.required,
        ok=status_code == spec.expected_status,
        status_code=status_code,
        error_message=None if status_code == spec.expected_status else "unexpected status",
    )


def _snapshot_from_powershell_item(item: dict[str, Any]) -> ProcessSnapshot:
    return ProcessSnapshot(
        pid=int(item.get("ProcessId") or 0),
        name=str(item.get("Name") or ""),
        command_line=str(item.get("CommandLine") or ""),
    )


def _snapshot_from_docker_json_line(line: str) -> ContainerSnapshot:
    item = json.loads(line)
    return ContainerSnapshot(
        name=str(item.get("Names") or item.get("Name") or ""),
        status=str(item.get("Status") or ""),
    )


def _command_matches(command_line: str, needles: Sequence[str]) -> bool:
    normalized_command = _normalize_command(command_line)
    return all(_normalize_command(needle) in normalized_command for needle in needles)


def _normalize_command(value: str) -> str:
    return " ".join(value.lower().split())


def _redact_command_line(command_line: str) -> str:
    redacted = re.sub(
        r"(?i)(\b[A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|API_KEY)[A-Z0-9_]*=)[^\s]+",
        r"\1<redacted>",
        command_line,
    )
    redacted = re.sub(
        r"(?i)(--(?:token|secret|password|api-key|auth-token|bot-token)\s+)[^\s]+",
        r"\1<redacted>",
        redacted,
    )
    return re.sub(
        r"(?i)(--(?:token|secret|password|api-key|auth-token|bot-token)=)[^\s]+",
        r"\1<redacted>",
        redacted,
    )
