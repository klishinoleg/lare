from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import httpx

from application.ai.reader_provider import (
    LocalReaderAiProvider,
    ReaderAiProvider,
    ReaderAiProviderResponse,
    ReaderDialogRequest,
    ReaderImageRequest,
    ReaderSegmentRequest,
    ReaderTextRequest,
    ReaderVoiceRequest,
    ReaderWordExplanationRequest,
    ReaderWordExplanationResponse,
)
from core.config import settings
from domain.text_data.enums import TextActionsTypes

WORD_TYPE_CODES = """\
- NS: Noun
- VER: Verb
- ADJ: Adjective
- ADV: Adverb
- PRN: Pronoun
- NUM: Numeral
- PRP: Preposition
- CON: Conjunction
- INT: Interjection
- PRT: Particle
- ART: Article
- GER: Gerund
- PAR: Participle
"""


class OpenAICompatibleReaderAiProvider:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        chat_model: str,
        image_model: str,
        speech_model: str,
        speech_voice: str,
        fallback: ReaderAiProvider | None = None,
        http_client: httpx.AsyncClient | None = None,
        voice_output_dir: Path | None = None,
        voice_public_prefix: str | None = None,
        image_size: str = "1024x1024",
        provider_name: str = "openai",
    ) -> None:
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.chat_model = chat_model
        self.image_model = image_model
        self.speech_model = speech_model
        self.speech_voice = speech_voice
        self.fallback = fallback or LocalReaderAiProvider()
        self.http_client = http_client
        self.voice_output_dir = voice_output_dir or settings.get_upload_dir() / "ai_voice"
        upload_url = settings.images_upload_url or "uploads"
        self.voice_public_prefix = (voice_public_prefix or f"{upload_url}/ai_voice").strip("/")
        self.image_size = image_size
        self.provider_name = provider_name

    async def process_segment(
        self,
        request: ReaderSegmentRequest,
    ) -> ReaderAiProviderResponse:
        if request.action == TextActionsTypes.VOICE:
            return await self.create_voice(
                ReaderVoiceRequest(
                    account_id=request.account_id,
                    entity="segment",
                    item_id=request.segment_id,
                    text=request.text,
                    fallback_file_path=f"uploads/segments/segment-{request.segment_id}.wav",
                )
            )
        return await self.translate_text(
            ReaderTextRequest(
                account_id=request.account_id,
                text=request.text,
                target_language_id=request.language_id,
                purpose=(request.translate_type.value if request.translate_type else "segment"),
            )
        )

    async def translate_text(self, request: ReaderTextRequest) -> ReaderAiProviderResponse:
        if not self.api_key:
            return await self.fallback.translate_text(request)

        payload = {
            "model": self.chat_model,
            "messages": self._translation_messages(request),
        }
        if self._translation_requires_json_response(request):
            payload["response_format"] = {"type": "json_object"}
        data = await self._post_json("chat/completions", payload)
        content = self._chat_content(data)
        if not content:
            return await self.fallback.translate_text(request)
        return ReaderAiProviderResponse(content=content, provider=self.provider_name)

    async def create_voice(self, request: ReaderVoiceRequest) -> ReaderAiProviderResponse:
        if not self.api_key:
            return await self.fallback.create_voice(request)

        payload = {
            "model": self.speech_model,
            "voice": self.speech_voice,
            "input": request.text,
            "response_format": "mp3",
        }
        content = await self._post_bytes("audio/speech", payload)
        if not content:
            return await self.fallback.create_voice(request)

        self.voice_output_dir.mkdir(parents=True, exist_ok=True)
        file_name = self._voice_file_name(request)
        file_path = self.voice_output_dir / file_name
        file_path.write_bytes(content)
        public_path = f"{self.voice_public_prefix}/{file_name}"
        return ReaderAiProviderResponse(
            content=public_path,
            provider=self.provider_name,
            file_path=public_path,
        )

    async def generate_image(self, request: ReaderImageRequest) -> ReaderAiProviderResponse:
        if not self.api_key:
            return await self.fallback.generate_image(request)

        prompt = (
            "Create a polished book cover image for Lazy Reader.\n"
            f"Title: {request.name}\n"
            f"Description: {request.description}"
        )
        payload = {
            "model": self.image_model,
            "prompt": prompt,
            "size": self.image_size,
            "response_format": "b64_json",
        }
        data = await self._post_json("images/generations", payload)
        source = self._image_source(data)
        if not source:
            return await self.fallback.generate_image(request)
        return ReaderAiProviderResponse(content=source, provider=self.provider_name)

    async def answer_dialog(self, request: ReaderDialogRequest) -> ReaderAiProviderResponse:
        if not self.api_key:
            return await self.fallback.answer_dialog(request)

        history = "\n".join(
            f"{item.get('role', 'message')}: {item.get('content', '')}"
            for item in request.history[-8:]
        )
        payload = {
            "model": self.chat_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a friendly language tutor inside Lazy Reader. "
                        "Explain clearly, briefly, and stay focused on the selected text."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Target language: {request.target_language_code or 'default'}\n"
                        f"Selected text: {request.text_part}\n"
                        f"Conversation:\n{history}\n"
                        f"User message: {request.message}"
                    ),
                },
            ],
        }
        data = await self._post_json("chat/completions", payload)
        content = self._chat_content(data)
        if not content:
            return await self.fallback.answer_dialog(request)
        return ReaderAiProviderResponse(content=content, provider=self.provider_name)

    async def explain_word(
        self,
        request: ReaderWordExplanationRequest,
    ) -> ReaderWordExplanationResponse:
        if not self.api_key:
            return await self.fallback.explain_word(request)

        payload = {
            "model": self.chat_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Explain word etymology for a language learner. "
                        "Return compact valid JSON only."
                    ),
                },
                {
                    "role": "user",
                    "content": self._word_explanation_prompt(request),
                },
            ],
            "response_format": {"type": "json_object"},
        }
        data = await self._post_json("chat/completions", payload)
        parsed = self._word_explanation(data)
        if parsed is None:
            return await self.fallback.explain_word(request)
        return parsed

    async def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        response = await self._post(path, json=payload)
        if response is None:
            return None
        try:
            return response.json()
        except ValueError:
            return None

    async def _post_bytes(self, path: str, payload: dict[str, Any]) -> bytes | None:
        response = await self._post(path, json=payload)
        if response is None:
            return None
        return response.content or None

    async def _post(self, path: str, *, json: dict[str, Any]) -> httpx.Response | None:
        if not self.api_key:
            return None
        try:
            if self.http_client is not None:
                response = await self.http_client.post(
                    self._url(path),
                    headers=self._headers(),
                    json=json,
                )
            else:
                async with httpx.AsyncClient(timeout=60) as client:
                    response = await client.post(
                        self._url(path),
                        headers=self._headers(),
                        json=json,
                    )
            response.raise_for_status()
            return response
        except httpx.HTTPError:
            return None

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def _translation_messages(self, request: ReaderTextRequest) -> list[dict[str, str]]:
        purpose = (request.purpose or "translate").lower()
        source = request.source_language_code or (
            str(request.source_language_id) if request.source_language_id else "auto"
        )
        target = request.target_language_code or str(request.target_language_id or "default")

        if "generation" in purpose:
            return [
                {
                    "role": "system",
                    "content": (
                        "You create language-learning reading material for Lazy Reader. "
                        "Follow the user's requested JSON schema exactly."
                    ),
                },
                {"role": "user", "content": request.text},
            ]

        if purpose in {"words", "full"}:
            include_translation = purpose == "full"
            return [
                {
                    "role": "system",
                    "content": (
                        "You are Lazy Reader's morphological analysis engine. "
                        "Return compact valid JSON only, with no Markdown fences. "
                        "Never translate into English unless English is the target language."
                    ),
                },
                {
                    "role": "user",
                    "content": self._word_analysis_prompt(
                        text=request.text,
                        source=source,
                        target=target,
                        include_translation=include_translation,
                    ),
                },
            ]

        if purpose == "word":
            task = (
                "Translate this single source-language word into the target language. "
                "Return only the most common learner-facing translation, no JSON."
            )
        else:
            task = (
                "Translate the selected source-language text into the target language. "
                "Return only the translated text, no JSON and no explanations."
            )
        return [
            {
                "role": "system",
                "content": "You are Lazy Reader's language assistant. Return only the requested text.",
            },
            {
                "role": "user",
                "content": (
                    f"{task}\n"
                    f"Original/source language: {source}\n"
                    f"Target language: {target}\n"
                    f"Text:\n{request.text}"
                ),
            },
        ]

    @staticmethod
    def _translation_requires_json_response(request: ReaderTextRequest) -> bool:
        purpose = (request.purpose or "translate").lower()
        return "generation" in purpose or purpose in {"words", "full"}

    @staticmethod
    def _word_analysis_prompt(
        *,
        text: str,
        source: str,
        target: str,
        include_translation: bool,
    ) -> str:
        keys = "`text`, `translate`, and `table`" if include_translation else "`text` and `table`"
        translation_rule = (
            "Include `translate`: the best full-sentence translation into the target language.\n"
            if include_translation
            else "Do not include a full-sentence translation.\n"
        )
        examples = ""
        if source.lower().startswith("fr") and target.lower().startswith("ru"):
            examples = (
                "\nExamples:\n\n"
                "Input: Extrait du Journal en français facile du 24 juin 2026\n"
                "Output:\n"
                '{"text":"Extrait du Journal en français facile du 24 juin 2026","table":['
                '{"word":"Extrait","translate":"отрывок","translit":"ɛkstʁɛ","type":"NS","gender":"m"},'
                '{"word":"du","translate":"из/от; de + le","translit":"dy","type":"ART","gender":"m"},'
                '{"word":"Journal","translate":"журнал; газета","translit":"ʒuʁnal","type":"NS","gender":"m"},'
                '{"word":"en","translate":"на; в","translit":"ɑ̃","type":"PRP","gender":""},'
                '{"word":"français","translate":"французском языке","translit":"fʁɑ̃sɛ","type":"NS","gender":"m"},'
                '{"word":"facile","translate":"лёгком; простом","translit":"fasil","type":"ADJ","gender":"m"},'
                '{"word":"du","translate":"от; de + le","translit":"dy","type":"ART","gender":"m"},'
                '{"word":"24","translate":"двадцать четыре","translit":"vɛ̃t katʁ","type":"NUM","gender":""},'
                '{"word":"juin","translate":"июнь","translit":"ʒɥɛ̃","type":"NS","gender":"m"},'
                '{"word":"2026","translate":"две тысячи двадцать шесть","translit":"dø mil vɛ̃t sis","type":"NUM","gender":""}'
                "]}\n\n"
                "Input: Nous habitons maintenant a Toulouse.\n"
                "Output:\n"
                '{"text":"Nous habitons maintenant a Toulouse.","table":['
                '{"word":"Nous","translate":"мы","translit":"nu","type":"PRN","gender":""},'
                '{"word":"habitons","translate":"живём","translit":"abitɔ̃","type":"VER","gender":""},'
                '{"word":"maintenant","translate":"сейчас","translit":"mɛ̃tnɑ̃","type":"ADV","gender":""},'
                '{"word":"a","translate":"в; нормативно à","translit":"a","type":"PRP","gender":""},'
                '{"word":"Toulouse","translate":"Тулуза","translit":"tuluz","type":"NS","gender":"f"}'
                "]}\n"
            )
        return (
            "Analyze the selected learner text.\n"
            f"Original/source language: {source}\n"
            f"Target language for translations and explanations: {target}\n"
            f"Required JSON keys: {keys}.\n"
            f"{translation_rule}"
            "Return exactly this JSON shape: "
            '{"text":"<original text exactly>","table":[{"word":"...","translate":"...",'
            '"translit":"...","type":"...","gender":"..."}]}\n'
            "Each table item must use exactly these keys: "
            "`word`, `translate`, `translit`, `type`, `gender`.\n"
            "Hard rules:\n"
            "1. `text` must be exactly the input text.\n"
            "2. `table` must contain exactly one row for each visible source-language word/token in order.\n"
            "3. Preserve `word` exactly as it appears in the input, including case and accents.\n"
            "4. Do not correct spelling, lemmatize, split, merge, or expand contractions.\n"
            "5. If the input has `du`, row.word must be `du`, not `de` and `le`.\n"
            "6. If the input has `habitons`, row.word must be `habitons`, not `habitions`.\n"
            "7. If French input has unaccented `a` before a place, interpret it as `à` in context, "
            "but keep row.word as `a`.\n"
            "8. `translate` must use only the target language and must fit the word in context.\n"
            "9. For function words and articles, explain the function concisely in the target language.\n"
            "10. For French, `translit` must be IPA pronunciation only, with no brackets and no Cyrillic transliteration.\n"
            "11. `type` must be one of these short codes:\n"
            f"{WORD_TYPE_CODES}"
            "12. `gender` must be `m`, `f`, `n`, or empty string. Use gender only when clear in context.\n"
            "13. Exclude pure punctuation. Include numbers as tokens with source-language pronunciation.\n"
            f"{examples}\n"
            "Now process this input:\n"
            f"{text}"
        )

    @staticmethod
    def _word_explanation_prompt(request: ReaderWordExplanationRequest) -> str:
        source = request.source_language_code or "auto"
        target = request.target_language_code or "default"
        return (
            "Analyze one source-language word for a language learner.\n"
            f"Original/source language of the word: {source}\n"
            f"Target language for translation, explanation, and descriptions: {target}\n"
            f"Word: {request.word}\n\n"
            "Return JSON with these keys:\n"
            "- `description`: brief definition and etymology in the target language.\n"
            "- `root_name`: root/base form in the source language.\n"
            "- `root_description`: short explanation of the root in the target language.\n"
            "- `parts`: array of components. Each item uses `name`, `type`, `description`.\n"
            "Part names stay in the source language; part descriptions are in the target language.\n"
            "If the word has prefix/suffix/root, include them as separate parts."
        )

    @staticmethod
    def _chat_content(data: dict[str, Any] | None) -> str | None:
        if not data:
            return None
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            return None
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        if not isinstance(message, dict):
            return None
        content = message.get("content")
        if not isinstance(content, str):
            return None
        content = content.strip()
        return content or None

    @staticmethod
    def _image_source(data: dict[str, Any] | None) -> str | None:
        if not data:
            return None
        items = data.get("data")
        if not isinstance(items, list) or not items or not isinstance(items[0], dict):
            return None
        b64_json = items[0].get("b64_json")
        if isinstance(b64_json, str) and b64_json:
            return f"data:image/png;base64,{b64_json}"
        url = items[0].get("url")
        if isinstance(url, str) and url:
            return url
        return None

    def _word_explanation(self, data: dict[str, Any] | None) -> ReaderWordExplanationResponse | None:
        content = OpenAICompatibleReaderAiProvider._chat_content(data)
        if not content:
            return None
        try:
            import json

            parsed = json.loads(content)
        except ValueError:
            return None
        if not isinstance(parsed, dict):
            return None

        description = parsed.get("description")
        root_name = parsed.get("root_name") or parsed.get("root")
        root_description = parsed.get("root_description")
        if not all(isinstance(item, str) and item for item in (description, root_name, root_description)):
            return None
        parts_raw = parsed.get("parts")
        parts: list[dict[str, str]] = []
        if isinstance(parts_raw, list):
            for item in parts_raw:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name") or "").strip()
                part_type = str(item.get("type") or "root").strip()
                part_description = str(item.get("description") or "").strip()
                if name:
                    parts.append(
                        {
                            "name": name,
                            "type": part_type or "root",
                            "description": part_description,
                        }
                    )
        for key, part_type in (("prefix", "prefix"), ("suffix", "postfix")):
            name = str(parsed.get(key) or "").strip()
            description_key = f"{key}_description"
            part_description = str(parsed.get(description_key) or "").strip()
            if name and name != "-":
                parts.append(
                    {
                        "name": name,
                        "type": part_type,
                        "description": part_description,
                    }
                )
        if not parts and root_name:
            parts.append(
                {
                    "name": root_name,
                    "type": "root",
                    "description": root_description,
                }
            )
        return ReaderWordExplanationResponse(
            description=description,
            root_name=root_name,
            root_description=root_description,
            parts=tuple(parts),
            provider=self.provider_name,
        )

    @staticmethod
    def _voice_file_name(request: ReaderVoiceRequest) -> str:
        safe_entity = re.sub(r"[^a-zA-Z0-9_-]+", "_", request.entity).strip("_") or "voice"
        return f"{safe_entity}_{request.item_id}.mp3"
