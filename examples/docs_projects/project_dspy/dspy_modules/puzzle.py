"""Puzzle data structures and game logic for NYTimes Connections."""

import csv
import random
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set

# Color to difficulty mapping
COLOR_TO_DIFFICULTY = {
    0: "yellow",  # easiest
    1: "green",
    2: "blue",
    3: "purple",  # hardest
}


# start_puzzle_dataclasses
@dataclass
class PuzzleGroup:
    """Represents a group in a Connections puzzle."""

    name: str
    color: str
    words: List[str]


@dataclass
class Puzzle:
    """Represents a complete Connections puzzle."""

    id: int
    date: str
    difficulty: float
    words: List[str]
    groups: List[PuzzleGroup]


@dataclass
class GameState:
    """Tracks the state of a game in progress."""

    puzzle: Puzzle
    solved_groups: Set[str]  # group colors that have been solved
    guess_count: int
    mistake_count: int
    invalid_count: int
    finished: bool
    won: bool
    start_time: Optional[float]
    end_time: Optional[float]


# end_puzzle_dataclasses


def create_game_state(puzzle: Puzzle) -> GameState:
    """Initialize a new game state for a given puzzle."""
    return GameState(
        puzzle=puzzle,
        solved_groups=set(),
        guess_count=0,
        mistake_count=0,
        invalid_count=0,
        finished=False,
        won=False,
        start_time=None,
        end_time=None,
    )


# start_load_puzzles_from_csv
def load_puzzles_from_csv(csv_path: Path) -> List[Puzzle]:
    """Load puzzles from CSV file format."""
    puzzles_dict = {}

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            game_id = int(row["Game ID"])
            puzzle_date = row["Puzzle Date"]
            word = row["Word"].upper()
            group_name = row["Group Name"]
            group_level = int(row["Group Level"])

            if game_id not in puzzles_dict:
                puzzles_dict[game_id] = {
                    "id": game_id,
                    "date": puzzle_date,
                    "words": [],
                    "groups": {},
                }

            puzzles_dict[game_id]["words"].append(word)

            if group_name not in puzzles_dict[game_id]["groups"]:
                puzzles_dict[game_id]["groups"][group_name] = {
                    "name": group_name,
                    "color": COLOR_TO_DIFFICULTY[group_level],
                    "words": [],
                }

            puzzles_dict[game_id]["groups"][group_name]["words"].append(word)

    # Convert to Puzzle objects
    puzzles = []
    for puzzle_data in puzzles_dict.values():
        groups = [
            PuzzleGroup(name=group["name"], color=group["color"], words=group["words"])
            for group in puzzle_data["groups"].values()
        ]

        # Calculate difficulty as average group level
        avg_difficulty = sum(
            list(COLOR_TO_DIFFICULTY.keys())[
                list(COLOR_TO_DIFFICULTY.values()).index(g.color)
            ]
            for g in groups
        ) / len(groups)

        puzzle = Puzzle(
            id=puzzle_data["id"],
            date=puzzle_data["date"],
            difficulty=avg_difficulty,
            words=puzzle_data["words"],
            groups=groups,
        )
        puzzles.append(puzzle)

    return puzzles


# end_load_puzzles_from_csv


class ConnectionsGameLogic:
    """Game logic for Connections puzzles."""

    MAX_MISTAKES = 4
    MAX_INVALID = 3
    ALLOWED_COLORS = {"blue", "yellow", "green", "purple"}

    # start_validate_puzzle
    @staticmethod
    def validate_puzzle(puzzle: Puzzle) -> None:
        """Validate puzzle data structure and constraints."""
        if len(puzzle.words) != 16:
            raise ValueError("Puzzle must contain exactly 16 words")

        if len(puzzle.groups) != 4:
            raise ValueError("Puzzle must contain exactly 4 groups")

        # Check colors
        colors = {group.color.lower() for group in puzzle.groups}
        if colors != ConnectionsGameLogic.ALLOWED_COLORS:
            raise ValueError(
                f"Group colors must be {ConnectionsGameLogic.ALLOWED_COLORS}"
            )

        # Check group sizes
        for i, group in enumerate(puzzle.groups):
            if len(group.words) != 4:
                raise ValueError(f"Group {i} must contain exactly 4 words")

        # Check for duplicate words across groups
        all_group_words = [w.upper() for group in puzzle.groups for w in group.words]
        if len(all_group_words) != len(set(all_group_words)):
            raise ValueError("Duplicate words found across groups")

        # Check that group words match puzzle words
        puzzle_words_upper = {w.upper() for w in puzzle.words}
        group_words_upper = set(all_group_words)
        if puzzle_words_upper != group_words_upper:
            raise ValueError("Group words must match puzzle words exactly")

    # end_validate_puzzle

    @staticmethod
    def parse_response(response: str) -> List[str]:
        """Parse response into list of words."""
        try:
            words = [word.strip().upper() for word in response.split(",")]
        except Exception as e:
            print(f"Error parsing response: {e}")
            return []
        return [word for word in words if word]  # Remove empty strings

    @staticmethod
    def validate_guess(state: GameState, words: List[str]) -> Optional[str]:
        """
        Validate a guess.
        Returns: Error message if invalid, None if valid
        """
        # Check word count
        if len(words) != 4:
            return f"Expected 4 words, got {len(words)}"

        # Check for duplicates
        if len(set(words)) != 4:
            return "Duplicate words not allowed"

        # Check if words are in puzzle
        puzzle_words = set(state.puzzle.words)
        for word in words:
            if word not in puzzle_words:
                return f"Word '{word}' not in puzzle"

        # Check if words are from already solved groups
        solved_words = set()
        for group in state.puzzle.groups:
            if group.color in state.solved_groups:
                solved_words.update(group.words)

        for word in words:
            if word in solved_words:
                return f"Word '{word}' is from an already solved group"

        return None

    @staticmethod
    def get_remaining_words(state: GameState) -> List[str]:
        """Get words that are still available (not from solved groups)."""
        solved_words = set()
        for group in state.puzzle.groups:
            if group.color in state.solved_groups:
                solved_words.update(group.words)

        all_words = set(state.puzzle.words)
        remaining_words = all_words - solved_words
        return list(remaining_words)

    # start_process_guess
    @staticmethod
    def process_guess(state: GameState, response: str) -> str:
        """
        Process a guess and update game state.
        Returns: Result string: "CORRECT", "INCORRECT", or detailed invalid response message
        """
        # Guard against processing guesses after game ends
        if state.finished:
            return "GAME_ALREADY_FINISHED"

        # Parse response
        words = ConnectionsGameLogic.parse_response(response)

        # Validate response
        validation_error = ConnectionsGameLogic.validate_guess(state, words)
        if validation_error:
            state.invalid_count += 1
            # Get remaining words (not from solved groups)
            remaining_words = ConnectionsGameLogic.get_remaining_words(state)
            invalid_message = f"INVALID_RESPONSE: {validation_error}. Available words: {', '.join(sorted(remaining_words))}. You provided: {', '.join(words) if words else 'no valid words'}"
            if state.invalid_count >= ConnectionsGameLogic.MAX_INVALID:
                state.finished = True
            return invalid_message

        # Check if guess is correct
        state.guess_count += 1

        for group in state.puzzle.groups:
            if set(words) == set(group.words):
                state.solved_groups.add(group.color)
                if len(state.solved_groups) >= 4:
                    state.finished = True
                    state.won = True
                    return "CORRECT"
                else:
                    return "CORRECT. NEXT GUESS?"

        # Incorrect guess
        state.mistake_count += 1
        if state.mistake_count >= ConnectionsGameLogic.MAX_MISTAKES:
            state.finished = True

        remaining_guesses = ConnectionsGameLogic.MAX_MISTAKES - state.mistake_count
        return f"INCORRECT. {remaining_guesses} INCORRECT GUESSES REMAINING"

    # end_process_guess


# start_shuffle_and_split_puzzles
def shuffle_and_split_puzzles(
    puzzles: List[Puzzle], train_ratio: float = 0.25, seed: int = 42
) -> tuple[List[Puzzle], List[Puzzle]]:
    """Shuffle puzzles and split into train/test sets."""
    random.seed(seed)
    shuffled = puzzles.copy()
    random.shuffle(shuffled)

    split_point = int(len(shuffled) * train_ratio)
    train_set = shuffled[:split_point]
    test_set = shuffled  # Test on all puzzles as requested

    return train_set, test_set


# end_shuffle_and_split_puzzles
