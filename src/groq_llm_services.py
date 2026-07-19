from groq import Groq
from pydantic import BaseModel, ValidationError

from src.chatbot.models.history import History
from src.chatbot.services.prompt_service import PromptService
from src.config import GROQ_API_KEY
from src.loggers import main_logger
from src.chatbot.models.llm_response_model import LLMResponseModel


class GroqModelName:
    COMPOUND = "groq/compound"
    COMPOUND_MINI = "groq/compound-mini"

    LLAMA_3_1_8B_INSTANT = "llama-3.1-8b-instant"
    LLAMA_3_3_70B_VERSATILE = "llama-3.3-70b-versatile"

    GPT_OSS_120B = "openai/gpt-oss-120b"
    GPT_OSS_20B = "openai/gpt-oss-20b"

    WHISPER_LARGE_V3 = "whisper-large-v3"
    WHISPER_LARGE_V3_TURBO = "whisper-large-v3-turbo"

    # Preview
    QWEN3_32B = 'qwen/qwen3-32b'
    QWEN_QWEN3_6_27B = 'qwen/qwen3.6-27b'

    META_LLAMA_LLAMA_4_SCOUT_17B_16E_INSTRUCT = 'meta-llama/llama-4-scout-17b-16e-instruct'
    META_LLAMA_LLAMA_PROMPT_GUARD_2_22M = 'meta-llama/llama-prompt-guard-2-22m'
    META_LLAMA_LLAMA_PROMPT_GUARD_2_86M = 'meta-llama/llama-prompt-guard-2-86m'

    OPENAI_GPT_OSS_SAFEGUARD_20B = 'openai/gpt-oss-safeguard-20b'


class GroqServices:
    def __init__(
            self,
            api_key: str = '',
            prompt_services=None,
    ):
        self.api_key = api_key or GROQ_API_KEY
        self.client = Groq(api_key=self.api_key)
        self.prompt_service = prompt_services or PromptService()

    def chat(
            self,
            text: str,
            model_name: str = GroqModelName.LLAMA_3_1_8B_INSTANT,
            system_prompt: str | None = None, response_format: dict | None = None,
    ) -> str:
        messages = []

        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })

        messages.append({
            "role": "user",
            "content": text
        })

        kwargs = {}

        if response_format is not None:
            kwargs["response_format"] = response_format

        response = self.client.chat.completions.create(
            model=model_name,
            messages=messages,
            **kwargs
        )

        return response.choices[0].message.content

    def chat_json(
            self,
            messages: list[dict],
            response_model: type[LLMResponseModel],
            model_name: str = GroqModelName.LLAMA_3_1_8B_INSTANT,
            system_prompt: str | None = None
    ) -> BaseModel:

        # lấy mô tả schema
        schema = response_model.llm_schema()

        # format prompt trả về json, truyển mô tả schema vào
        prompt = self.prompt_service.render(
            "json_output",
            schema=schema
        )

        # Nếu không có system prompt
        system_content = prompt

        # nếu có system prompt
        if system_prompt:
            system_content = f"{system_prompt}\n\n{prompt}"

        messages = [
            {
                "role": "system",
                "content": system_content
            },
            *messages
        ]

        response = self.client.chat.completions.create(
            model=model_name,
            messages=messages,
            response_format={"type": "json_object"}
        )

        try:
            return response_model.model_validate_json(
                response.choices[0].message.content
            )
        except ValidationError as e:
            main_logger.exception(e)
            raise

    def chat_history(
            self,
            messages: list[dict[str, str]],
            model_name: str = GroqModelName.LLAMA_3_1_8B_INSTANT,
    ) -> str:
        response = self.client.chat.completions.create(
            model=model_name,
            messages=messages
        )

        return response.choices[0].message.content
