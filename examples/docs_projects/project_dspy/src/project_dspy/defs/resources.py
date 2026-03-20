"""Resources for the transcript analyzer project."""

from pathlib import Path

import dspy
from dagster import ConfigurableResource, get_dagster_logger
from pydantic import Field

from config import settings

logger = get_dagster_logger()


class GeminiResource(ConfigurableResource):
    """Google Gemini API client resource."""

    api_key: str = Field(description="Gemini API key")
    model: str = Field(
        default="gemini-2.0-flash-exp", description="Default model to use"
    )
    max_tokens: int = Field(default=8192, description="Default max tokens")
    temperature: float = Field(default=0.7, description="Default temperature")

    def get_model_config(self) -> dict:
        """Get model configuration for DSPy."""
        return {
            "model": f"gemini/{self.model}",
            "api_key": self.api_key,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }


class DSPyResource(ConfigurableResource):
    """DSPy model management resource."""

    models_directory: str = Field(description="Directory to store DSPy models")
    gemini_api_key: str = Field(description="Gemini API key for DSPy")
    model_name: str = Field(
        default="gemini-2.0-flash-exp", description="LM model for DSPy"
    )
    max_tokens: int = Field(default=8192, description="Max tokens for DSPy")
    temperature: float = Field(default=0.7, description="Temperature for DSPy")

    # start_configure_dspy
    def configure_dspy(self) -> None:
        """Configure DSPy with Gemini language model."""
        lm = dspy.LM(
            model=f"gemini/{self.model_name}",
            api_key=self.gemini_api_key,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        dspy.configure(lm=lm)
        logger.info(f"Configured DSPy with Gemini {self.model_name}")

    # end_configure_dspy

    def get_models_path(self) -> Path:
        """Get path to models directory."""
        models_path = Path(self.models_directory)
        models_path.mkdir(parents=True, exist_ok=True)
        return models_path

    # start_save_model
    def save_model(
        self, model: dspy.Module, model_name: str, version: str = "latest"
    ) -> Path:
        """Save DSPy model to disk."""
        models_path = self.get_models_path()
        model_file = models_path / f"{model_name}_{version}.pkl"
        model.save(model_file, save_program=False)
        logger.info(f"Saved model to {model_file}")
        return model_file

    # end_save_model

    def load_model(self, model: dspy.Module, model_name: str, version: str = "latest"):
        """Load DSPy model from disk."""
        models_path = self.get_models_path()
        model_file = models_path / f"{model_name}_{version}.pkl"

        if not model_file.exists():
            raise FileNotFoundError(f"Model not found: {model_file}")
        model.load(model_file)

        logger.info(f"Loaded model from {model_file}")
        return model


gemini_resource = GeminiResource(
    api_key=settings.gemini_api_key,
    model=settings.gemini_model,
    max_tokens=settings.gemini_max_tokens,
    temperature=settings.gemini_temperature,
)

dspy_resource = DSPyResource(
    models_directory=str(settings.models_dir),
    gemini_api_key=settings.gemini_api_key,
    model_name=settings.gemini_model,
    max_tokens=settings.gemini_max_tokens,
    temperature=settings.gemini_temperature,
)
