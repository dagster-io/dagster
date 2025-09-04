# Schema Models Documentation

## Pydantic Usage Note

The models in this schemas package use Pydantic `BaseModel` instead of the standard Dagster `@record` decorator to ensure compatibility with FastAPI/REST APIs which expect Pydantic models for JSON serialization/deserialization.

This is an intentional deviation from the standard Dagster coding conventions documented in the main project's `CLAUDE.md` file.
