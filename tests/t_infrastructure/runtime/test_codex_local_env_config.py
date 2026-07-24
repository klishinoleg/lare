from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_codex_compose_loads_ignored_secret_env_for_backend_services() -> None:
    compose = (ROOT / "tests_env" / "docker-compose.codex-local.yml").read_text(encoding="utf-8")

    assert "env_file: &codex_backend_env_files" in compose
    assert "path: ./codex-local.env" in compose
    assert "env_file: *codex_backend_env_files" in compose
    assert "./secrets:/workspace/secrets:ro" in compose
    assert "READER_AI_PROVIDER: local" not in compose


def test_codex_docker_build_context_excludes_env_files() -> None:
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")

    assert "*.env" in dockerignore
    assert "app/.env" in dockerignore
    assert "tests_env/secrets/" in dockerignore


def test_codex_secret_env_template_documents_deepseek_and_google_tts() -> None:
    template = (ROOT / "tests_env" / "codex-local.env.example").read_text(encoding="utf-8")

    assert "READER_AI_PROVIDER=deepseek" in template
    assert "READER_AI_OPENAI_BASE_URL=https://api.deepseek.com" in template
    assert "READER_AI_OPENAI_CHAT_MODEL=deepseek-v4-flash" in template
    assert "READER_AI_VOICE_PROVIDER=google" in template
    assert "GOOGLE_APPLICATION_CREDENTIALS=" in template
