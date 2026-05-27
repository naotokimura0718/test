"""環境変数と設定値の読み込み。"""

from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """プロジェクトの設定。"""

    anthropic_api_key: str = Field(alias="ANTHROPIC_API_KEY")
    claude_model: str = Field(default="claude-sonnet-4-6", alias="CLAUDE_MODEL")

    drawings_dir: Path = Field(default=Path("./data/drawings"), alias="DRAWINGS_DIR")
    ground_truth_dir: Path = Field(
        default=Path("./data/ground_truth"), alias="GROUND_TRUTH_DIR"
    )
    reference_dir: Path = Field(default=Path("./data/reference"), alias="REFERENCE_DIR")
    results_dir: Path = Field(default=Path("./results"), alias="RESULTS_DIR")

    target_estimation_error: float = Field(default=0.10, alias="TARGET_ESTIMATION_ERROR")
    target_structural_precision: float = Field(
        default=0.70, alias="TARGET_STRUCTURAL_PRECISION"
    )
    target_structural_recall: float = Field(
        default=0.50, alias="TARGET_STRUCTURAL_RECALL"
    )

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")


settings = Settings()
