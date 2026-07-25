from groq import Groq
from src import config

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
    ):
        api_key = api_key or config.GROQ_API_KEY
        self.client = Groq(api_key=api_key)
        self.DEFAUL_MODEL = GroqModelName.LLAMA_3_1_8B_INSTANT

    def hischat(self, messages: list[dict], model_name: str | None = None, json_mode: bool = False):
        kwargs = {
            'messages': messages,
            'model': model_name if model_name else self.DEFAUL_MODEL,
        }
        if json_mode:
            kwargs['response_format'] = {
                'type': 'json_object',
            }
        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message

    def chat(self, message: str, model_name: str | None = None, json_mode: bool = False):
        messages = [
            {
                'role': 'user',
                'content': message,
            }
        ]
        return self.hischat(messages, model_name, json_mode)


if __name__ == '__main__':
    messages = [
        {
            'role': 'user',
            'content': 'Xin chào'
        }
    ]

    gs = GroqServices()
    msg = gs.hischat(messages)
    print(f'-{msg.role}:\n{msg.content}')
