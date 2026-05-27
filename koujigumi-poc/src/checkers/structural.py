"""構造的成立性チェック（差別化の核）。"""

from pathlib import Path

from PIL import Image

from src.prompts.check_structural import CHECK_STRUCTURAL_SYSTEM, make_user_prompt
from src.readers.pdf_reader import pdf_to_images
from src.readers.vision_reader import ask_claude_with_images
from src.schemas import StructuralCheckReport


async def run_structural_check(
    pdf_path: Path,
    project_name: str,
    page_range: tuple[int, int] | None = None,
) -> StructuralCheckReport:
    """
    PDFに対して構造チェックを実行する。

    Args:
        pdf_path: チェック対象のPDFパス
        project_name: 物件名（プロンプトに埋め込む）
        page_range: (first_page, last_page) を1-indexedで指定。Noneなら全ページ

    Returns:
        構造チェックレポート
    """
    first, last = page_range if page_range else (None, None)
    images = pdf_to_images(pdf_path, dpi=200, first_page=first, last_page=last)

    user_prompt = make_user_prompt(project_name)

    report = await ask_claude_with_images(
        images=images,
        system_prompt=CHECK_STRUCTURAL_SYSTEM,
        user_prompt=user_prompt,
        response_model=StructuralCheckReport,
        max_tokens=8192,
    )

    return report


async def run_structural_check_on_images(
    images: list[Image.Image],
    project_name: str,
) -> StructuralCheckReport:
    """画像リストを直接受け取るバージョン（複数PDFを統合する場合等）。"""
    user_prompt = make_user_prompt(project_name)

    return await ask_claude_with_images(
        images=images,
        system_prompt=CHECK_STRUCTURAL_SYSTEM,
        user_prompt=user_prompt,
        response_model=StructuralCheckReport,
        max_tokens=8192,
    )
