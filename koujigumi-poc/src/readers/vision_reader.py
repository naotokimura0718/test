"""Claude Vision APIを呼び出すラッパー。"""

import json
from typing import TypeVar

from anthropic import AsyncAnthropic
from PIL import Image
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings
from src.readers.pdf_reader import prepare_claude_image_input

T = TypeVar("T", bound=BaseModel)

_client: AsyncAnthropic | None = None


def get_client() -> AsyncAnthropic:
    """Claude APIクライアントのシングルトン。"""
    global _client
    if _client is None:
        _client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def ask_claude_with_images(
    images: list[Image.Image],
    system_prompt: str,
    user_prompt: str,
    response_model: type[T],
    max_tokens: int = 4096,
) -> T:
    """
    画像つきでClaudeに問い合わせ、構造化データで返す。

    Args:
        images: Claude Visionに渡す画像のリスト
        system_prompt: System プロンプト
        user_prompt: User プロンプト
        response_model: 期待するPydanticモデル
        max_tokens: 最大出力トークン数

    Returns:
        response_model のインスタンス
    """
    image_inputs = [prepare_claude_image_input(img) for img in images]

    # Pydanticモデルのスキーマをプロンプトに埋め込んで、JSON出力を強制する
    schema = response_model.model_json_schema()
    full_user_prompt = f"""{user_prompt}

回答は以下のJSON Schemaに厳密に従って、JSONオブジェクトのみを返してください。
前置きや説明、markdownのコードブロックは不要です。

```json
{json.dumps(schema, ensure_ascii=False, indent=2)}
```
"""

    client = get_client()
    response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": [
                    *image_inputs,
                    {"type": "text", "text": full_user_prompt},
                ],
            }
        ],
    )

    # 応答からテキストを抽出
    text = "".join(block.text for block in response.content if block.type == "text")

    # JSONパース（markdownコードブロックに包まれている場合の対処）
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if len(lines) > 2 else text

    data = json.loads(text)
    return response_model.model_validate(data)
