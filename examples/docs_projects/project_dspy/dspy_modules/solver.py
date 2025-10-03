"""DSPy solver for Connections puzzles."""

import time
from typing import List

import dspy

from .puzzle import ConnectionsGameLogic, Puzzle, create_game_state

# start_game_rules
# Game rules
GAME_RULES = """
HOW TO PLAY
1. Guess 4 related words.
2. You'll be told "CORRECT", "INCORRECT", or "INVALID_RESPONSE" with details.
3. If a word has been correctly guessed, it shall not be used again.
4. If invalid, you'll see available words and what went wrong.
5. You have at most 6 total guesses (4 mistakes allowed).

Respond with EXACTLY four words, ALL CAPS, comma-separated.
""".strip()
# end_game_rules


# start_connections_solver
class ConnectionsSolver(dspy.Module):
    """DSPy module for solving Connections puzzles."""

    def __init__(self):
        self.predict = dspy.ChainOfThought(
            "rules, available_words, history_feedback, guess_index -> guess"
        )
        self.logic = ConnectionsGameLogic()

    # end_connections_solver

    # start_forward_method
    def forward(self, puzzle: Puzzle) -> dspy.Prediction:
        """
        Solve a single puzzle and return results.

        Returns:
            dspy.Prediction: Results including success, attempts, time, etc.
        """
        state = create_game_state(puzzle)
        state.start_time = time.time()

        history_feedback = []
        guess_index = 0

        # start_solving_loop
        while not state.finished and guess_index < 10:  # Safety limit
            guess_index += 1

            # Get available words
            available_words = self.logic.get_remaining_words(state)
            available_words_str = ", ".join(sorted(available_words))

            # Generate guess using DSPy Chain-of-Thought
            prediction = self.predict(
                rules=GAME_RULES,
                available_words=available_words_str,
                history_feedback=" | ".join(history_feedback)
                if history_feedback
                else "No previous guesses",
                guess_index=guess_index,
            )

            # Process the guess and update game state
            result = self.logic.process_guess(state, prediction.guess.strip())
            history_feedback.append(
                f"Guess {guess_index}: '{prediction.guess.strip()}' -> {result}"
            )
        # end_solving_loop

        state.end_time = time.time()

        # start_return_results
        return dspy.Prediction(
            puzzle_id=puzzle.id,
            puzzle_date=puzzle.date,
            success=state.won,
            attempts=state.guess_count,
            mistakes=state.mistake_count,
            invalid_responses=state.invalid_count,
            groups_solved=len(state.solved_groups),
            duration=state.end_time - state.start_time if state.start_time else 0,
            finished=state.finished,
        )
        # end_return_results


# start_create_dataset
def create_dataset(puzzles: List[Puzzle]) -> List[dspy.Example]:
    """Convert puzzles to DSPy examples."""
    examples = []
    for puzzle in puzzles:
        example = dspy.Example(puzzle=puzzle, puzzle_id=puzzle.id).with_inputs("puzzle")
        examples.append(example)
    return examples


# end_create_dataset


# start_connections_success_metric
def connections_success_metric(example, pred, trace=None) -> float:
    """Metric function for DSPy evaluation."""
    if not hasattr(pred, "success"):
        return 0.0
    return 1.0 if pred.success else 0.0


# end_connections_success_metric
