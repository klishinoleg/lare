from __future__ import annotations

import importlib
from pathlib import Path

from application.events.event_types import SegmentEvents


def test_kafka_segment_entrypoint_exposes_faststream_app() -> None:
    module = importlib.import_module("interfaces.event_broker.kafka_segment")

    assert module.app is module.broker.app


def test_kafka_runtime_config_declares_segment_topics_and_worker() -> None:
    repo_root = Path(__file__).parents[3]
    topics = (repo_root / "tests_env" / "kafka" / "topics.conf").read_text()
    compose = (repo_root / "tests_env" / "docker-compose.yml").read_text()

    for event_type in SegmentEvents:
        assert f"{event_type.value}=" in topics

    assert "kafka_worker_segment:" in compose
    assert "interfaces.event_broker.kafka_segment:app" in compose


def test_kafka_topic_scripts_use_unix_line_endings() -> None:
    repo_root = Path(__file__).parents[3]

    for script_name in ("create-topics.sh", "change-topics.sh"):
        script = repo_root / "tests_env" / "kafka" / script_name
        data = script.read_bytes()
        assert data.startswith(b"#!/bin/bash\n")
        assert b"\r\n" not in data
