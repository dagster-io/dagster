"""Configuration management for the DSPy + Dagster Connections project."""

import os
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Project settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Google Gemini Configuration
    gemini_api_key: str = Field(default="", env="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.0-flash-exp", env="GEMINI_MODEL")
    gemini_judge_model: str = Field(
        default="gemini-2.0-flash-exp", env="GEMINI_JUDGE_MODEL"
    )
    gemini_max_tokens: int = Field(default=8192, env="GEMINI_MAX_TOKENS")
    gemini_temperature: float = Field(default=0.7, env="GEMINI_TEMPERATURE")

    # Connections Data Configuration
    connections_data_path: str = Field(
        default="./data/Connections_Data.csv", env="CONNECTIONS_DATA_PATH"
    )

    # Dagster Configuration
    dagster_home: str = Field(default="/tmp/dagster_home", env="DAGSTER_HOME")
    dagster_host: str = Field(default="localhost", env="DAGSTER_HOST")
    dagster_port: int = Field(default=3000, env="DAGSTER_PORT")

    # DSPy Configuration
    dspy_optimizer: Literal[
        "MIPROv2", "BootstrapFewShot", "BootstrapFewShotWithRandomSearch"
    ] = Field(default="MIPROv2", env="DSPY_OPTIMIZER")
    # start_dspy_auto_mode
    dspy_auto_mode: Literal["light", "medium", "heavy"] = Field(
        default="light", env="DSPY_AUTO_MODE"
    )
    # end_dspy_auto_mode
    dspy_min_samples: int = Field(default=10, env="DSPY_MIN_SAMPLES")
    # start_dspy_performance_threshold
    dspy_performance_threshold: float = Field(
        default=0.3, env="DSPY_PERFORMANCE_THRESHOLD"
    )
    dspy_improvement_threshold: float = Field(
        default=0.05, env="DSPY_IMPROVEMENT_THRESHOLD"
    )
    # end_dspy_performance_threshold

    # Connections Puzzle Configuration
    train_test_split: float = Field(default=0.25, env="TRAIN_TEST_SPLIT")
    # start_eval_subset_size
    eval_subset_size: int = Field(default=50, env="EVAL_SUBSET_SIZE")
    max_puzzle_attempts: int = Field(default=6, env="MAX_PUZZLE_ATTEMPTS")
    # end_eval_subset_size
    max_invalid_responses: int = Field(default=3, env="MAX_INVALID_RESPONSES")

    # Monitoring & Optimization
    # start_enable_optimization
    enable_optimization: bool = Field(default=True, env="ENABLE_OPTIMIZATION")
    optimization_schedule: str = Field(default="0 2 * * *", env="OPTIMIZATION_SCHEDULE")
    # end_enable_optimization
    # start_accuracy_alert_threshold
    accuracy_alert_threshold: float = Field(
        default=0.65, env="ACCURACY_ALERT_THRESHOLD"
    )
    # end_accuracy_alert_threshold

    # Streamlit Configuration
    streamlit_port: int = Field(default=8501, env="STREAMLIT_PORT")
    streamlit_theme: Literal["light", "dark"] = Field(
        default="light", env="STREAMLIT_THEME"
    )

    # Demo Mode
    demo_mode: bool = Field(default=False, env="DEMO_MODE")
    use_cached_results: bool = Field(default=True, env="USE_CACHED_RESULTS")
    mock_api_calls: bool = Field(default=False, env="MOCK_API_CALLS")

    # Paths
    data_dir: Path = Field(default=Path("./data"), env="DATA_DIR")
    models_dir: Path = Field(default=Path("./models"), env="MODELS_DIR")
    logs_dir: Path = Field(default=Path("./logs"), env="LOGS_DIR")

    @field_validator("data_dir", "models_dir", "logs_dir", mode="before")
    @classmethod
    def create_directories(cls, v):
        """Ensure directories exist."""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @field_validator("gemini_api_key")
    @classmethod
    def validate_api_key(cls, v):
        """Validate Gemini API key is provided."""
        if not v and not os.getenv("MOCK_API_CALLS", "false").lower() == "true":
            raise ValueError(
                "GEMINI_API_KEY must be set in environment variables or .env file"
            )
        return v

    @property
    def connections_csv_path(self) -> Path:
        """Path to Connections CSV data file."""
        return Path(self.connections_data_path)

    @property
    def model_checkpoint_dir(self) -> Path:
        """Directory for DSPy model checkpoints."""
        return self.models_dir / "checkpoints"

    # start_get_dspy_lm_config
    def get_dspy_lm_config(self) -> dict:
        """Get DSPy language model configuration for Gemini."""
        return {
            "model": f"gemini/{self.gemini_model}",
            "api_key": self.gemini_api_key,
            "max_tokens": self.gemini_max_tokens,
            "temperature": self.gemini_temperature,
        }

    # end_get_dspy_lm_config

    # start_get_optimizer_config
    def get_optimizer_config(self) -> dict:
        """Get DSPy optimizer configuration."""
        return {
            "optimizer": self.dspy_optimizer,
            "auto_mode": self.dspy_auto_mode,
            "min_samples": self.dspy_min_samples,
            "performance_threshold": self.dspy_performance_threshold,
            "improvement_threshold": self.dspy_improvement_threshold,
        }

    # end_get_optimizer_config


# Create global settings instance
settings = Settings()
