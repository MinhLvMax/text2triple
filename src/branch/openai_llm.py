import requests
import asyncio
from typing import Literal, TypedDict
from src.config import Config

Role = Literal["system", "user", "assistant"]


class Message(TypedDict):
    role: Role
    content: str


class LLM:
    def __init__(self, apikey: str | None = None, model: str | None = None, base_url: str | None = None):
        self._api_key = apikey or Config.OPEN_API_KEY
        self._model = model or "claude-opus-4-8"
        self._base_url = base_url or "https://danglamgiau.com/v1/chat/completions"

    async def complete(self, messeges: list[Message], system_msg: str | None = None):
        '''Phương thức chat'''

        # Nếu có system mess thì thêm vào
        if system_msg:
            messeges.append({
                'role': 'system',
                'content': system_msg,
            })

        r = requests.post(
            self._base_url,
            headers={
                "Authorization": f"Bearer {Config.OPEN_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": self._model,
                "messages": messeges,
                "stream": False,
            },
            timeout=120,
        )
        r = r.json()
        return r


async def main():
    msgs: list[Message] = [
        {
            'role': 'user',
            'content': 'Xin chào'
        }
    ]
    llm = LLM()
    outp = await llm.complete(
        messeges=msgs
    )
    from pprint import pprint
    pprint(outp)


if __name__ == '__main__':
    '''Test'''
    asyncio.run(main())
