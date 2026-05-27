"""PDF読み取り（PDFを画像に変換してClaude Visionに渡す準備）。"""

import base64
from pathlib import Path

from pdf2image import convert_from_path
from PIL import Image


def pdf_to_images(
    pdf_path: Path,
    dpi: int = 200,
    first_page: int | None = None,
    last_page: int | None = None,
) -> list[Image.Image]:
    """
    PDFを画像リストに変換する。

    Args:
        pdf_path: 入力PDFのパス
        dpi: 解像度（高精度を求める場合は300）
        first_page: 開始ページ（1-indexed）
        last_page: 終了ページ（1-indexed）

    Returns:
        PIL Image のリスト（各ページ）
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    return convert_from_path(
        str(pdf_path),
        dpi=dpi,
        first_page=first_page,
        last_page=last_page,
    )


def image_to_base64(image: Image.Image, fmt: str = "PNG") -> str:
    """
    PIL Image を base64 文字列に変換。Claude API に渡す形式。

    Args:
        image: PIL Image オブジェクト
        fmt: PNG または JPEG

    Returns:
        base64エンコードされた文字列
    """
    from io import BytesIO

    buffer = BytesIO()
    image.save(buffer, format=fmt)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def prepare_claude_image_input(image: Image.Image) -> dict:
    """
    Claude API のメッセージフォーマットに変換。

    Returns:
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": "...",
            },
        }
    """
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/png",
            "data": image_to_base64(image, fmt="PNG"),
        },
    }
