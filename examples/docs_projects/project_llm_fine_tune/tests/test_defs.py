import json

import dagster as dg
from dagster import AssetKey
from project_llm_fine_tune.definitions import defs as _raw_defs
from project_llm_fine_tune.defs.assets import (
    CATEGORIES,
    create_prompt_record,
    read_openai_file,
    write_openai_file,
)

defs: dg.Definitions = _raw_defs() if not isinstance(_raw_defs, dg.Definitions) else _raw_defs


def test_defs_load():
    assert isinstance(defs, dg.Definitions)


def test_assets_defined():
    repo = defs.get_repository_def()
    asset_keys = set(repo.assets_defs_by_key.keys())
    assert AssetKey("graphic_novels") in asset_keys
    assert AssetKey("authors") in asset_keys
    assert AssetKey("training_file") in asset_keys


def test_create_prompt_record_structure():
    data = {
        "title": "The Sandman",
        "author": "Neil Gaiman",
        "description": "A dream lord escapes captivity.",
        "category": "fantasy",
    }
    record = create_prompt_record(data, CATEGORIES)
    messages = record["messages"]
    assert len(messages) == 3
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[2]["role"] == "assistant"
    assert messages[2]["content"] == "fantasy"
    assert messages[2]["weight"] == 1


def test_create_prompt_record_includes_title_and_author():
    data = {
        "title": "Maus",
        "author": "Art Spiegelman",
        "description": "A Holocaust memoir in comic form.",
        "category": "drama",
    }
    record = create_prompt_record(data, CATEGORIES)
    user_message = record["messages"][1]["content"]
    assert "Maus" in user_message
    assert "Art Spiegelman" in user_message


def test_write_and_read_openai_file(tmp_path):
    file_path = str(tmp_path / "test.jsonl")
    records = [
        {"messages": [{"role": "user", "content": "hello"}]},
        {"messages": [{"role": "user", "content": "world"}]},
    ]
    write_openai_file(file_path, records)
    loaded = list(read_openai_file(file_path))
    assert len(loaded) == 2
    assert loaded[0]["messages"][0]["content"] == "hello"
    assert loaded[1]["messages"][0]["content"] == "world"


def test_write_openai_file_produces_valid_jsonl(tmp_path):
    file_path = str(tmp_path / "output.jsonl")
    records = [{"key": "val1"}, {"key": "val2"}]
    write_openai_file(file_path, records)
    with open(file_path) as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    assert len(lines) == 2
    for line in lines:
        json.loads(line)  # should not raise
