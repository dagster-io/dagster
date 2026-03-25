"""Tests for project_dspy — defs loading and pure Python game logic."""

import dagster as dg

from dspy_modules.puzzle import (
    ConnectionsGameLogic,
    Puzzle,
    PuzzleGroup,
    create_game_state,
)
from project_dspy.definitions import defs


def test_defs_load():
    assert isinstance(defs, dg.Definitions)


def test_resources_defined():
    repo = defs.get_repository_def()
    assert repo is not None


def _make_puzzle() -> Puzzle:
    groups = [
        PuzzleGroup("Fruits", "yellow", ["APPLE", "BANANA", "CHERRY", "DATE"]),
        PuzzleGroup("Colors", "green", ["RED", "BLUE", "GREEN", "YELLOW"]),
        PuzzleGroup("Animals", "blue", ["CAT", "DOG", "FISH", "BIRD"]),
        PuzzleGroup("Shapes", "purple", ["CIRCLE", "SQUARE", "TRIANGLE", "OVAL"]),
    ]
    words = [w for g in groups for w in g.words]
    return Puzzle(id=1, date="2024-01-01", difficulty=1.5, words=words, groups=groups)


def test_create_game_state_initial_values():
    puzzle = _make_puzzle()
    state = create_game_state(puzzle)
    assert state.guess_count == 0
    assert state.mistake_count == 0
    assert state.finished is False
    assert state.won is False
    assert len(state.solved_groups) == 0


def test_validate_puzzle_passes_for_valid_puzzle():
    puzzle = _make_puzzle()
    ConnectionsGameLogic.validate_puzzle(puzzle)  # should not raise


def test_process_guess_correct():
    puzzle = _make_puzzle()
    state = create_game_state(puzzle)
    result = ConnectionsGameLogic.process_guess(state, "APPLE, BANANA, CHERRY, DATE")
    assert result.startswith("CORRECT")
    assert "yellow" in state.solved_groups


def test_process_guess_incorrect():
    puzzle = _make_puzzle()
    state = create_game_state(puzzle)
    result = ConnectionsGameLogic.process_guess(state, "APPLE, RED, CAT, CIRCLE")
    assert "INCORRECT" in result
    assert state.mistake_count == 1


def test_process_guess_invalid_word_count():
    puzzle = _make_puzzle()
    state = create_game_state(puzzle)
    result = ConnectionsGameLogic.process_guess(state, "APPLE, BANANA, CHERRY")
    assert "INVALID_RESPONSE" in result


def test_parse_response_uppercases_words():
    words = ConnectionsGameLogic.parse_response("apple, Banana, CHERRY, date")
    assert words == ["APPLE", "BANANA", "CHERRY", "DATE"]
