"""Simple evaluation metrics for Connections puzzle solving based on game results."""

from typing import Any, Dict


# start_evaluate_connections_performance
def evaluate_connections_performance(puzzle, pred) -> Dict[str, Any]:
    """Comprehensive evaluation of Connections puzzle performance based on game output."""
    try:
        # Extract performance metrics directly from prediction
        success = getattr(pred, "success", False)
        attempts_used = getattr(pred, "attempts", 0)
        mistakes = getattr(pred, "mistakes", 0)
        invalid_responses = getattr(pred, "invalid_responses", 0)
        groups_solved = getattr(pred, "groups_solved", 0)
        duration = getattr(pred, "duration", 0.0)

        # Calculate derived metrics
        success_rate = 1.0 if success else 0.0

        # Strategy score: fewer attempts and mistakes = better strategy
        # Perfect score (1.0) for solving in 4 attempts with no mistakes
        if success:
            strategy_score = max(0.0, 1.0 - (attempts_used - 4) * 0.1 - mistakes * 0.2)
        else:
            # Partial credit for groups solved even if not completed
            strategy_score = groups_solved / 4.0 * 0.5  # Max 0.5 for partial completion

        # Efficiency score: based on attempts and time
        max_attempts = 6
        if success and attempts_used <= 4:
            efficiency_score = 1.0
        elif success:
            efficiency_score = max(0.0, 1.0 - (attempts_used - 4) / (max_attempts - 4))
        else:
            efficiency_score = 0.0

        # Reasoning score: combination of low mistakes and invalid responses
        total_errors = mistakes + invalid_responses
        reasoning_score = max(0.0, 1.0 - total_errors * 0.25)

        # Overall quality: weighted combination of all factors
        if success:
            overall_quality = (
                0.4 * success_rate
                + 0.3 * strategy_score
                + 0.2 * efficiency_score
                + 0.1 * reasoning_score
            )
        else:
            # For failed attempts, focus on partial progress
            overall_quality = (
                0.5 * (groups_solved / 4.0)
                + 0.3 * reasoning_score
                + 0.2 * min(attempts_used / max_attempts, 1.0)
            )

        return {
            "success": success,
            "success_rate": success_rate,
            "attempts_used": attempts_used,
            "mistakes": mistakes,
            "invalid_responses": invalid_responses,
            "groups_solved": groups_solved,
            "duration": duration,
            "strategy_score": strategy_score,
            "reasoning_score": reasoning_score,
            "efficiency_score": efficiency_score,
            "overall_quality": overall_quality,
        }

    except Exception as e:
        print(f"Error in evaluate_connections_performance: {e}")
        return {
            "success": False,
            "success_rate": 0.0,
            "attempts_used": 0,
            "mistakes": 0,
            "invalid_responses": 0,
            "groups_solved": 0,
            "duration": 0.0,
            "strategy_score": 0.0,
            "reasoning_score": 0.0,
            "efficiency_score": 0.0,
            "overall_quality": 0.0,
        }


# end_evaluate_connections_performance


def connections_success_metric(example, pred, trace=None) -> float:
    """Simple success metric for Connections puzzles - matches the provided success_metric."""
    if not hasattr(pred, "success"):
        return 0.0
    return 1.0 if pred.success else 0.0


def strategy_score(example, pred, trace=None) -> float:
    """Score the strategy quality based on attempts and mistakes."""
    try:
        success = getattr(pred, "success", False)
        attempts = getattr(pred, "attempts", 0)
        mistakes = getattr(pred, "mistakes", 0)
        groups_solved = getattr(pred, "groups_solved", 0)

        if success:
            # Perfect score for solving in 4 attempts with no mistakes
            return max(0.0, 1.0 - (attempts - 4) * 0.1 - mistakes * 0.2)
        else:
            # Partial credit for groups solved
            return groups_solved / 4.0 * 0.5

    except Exception:
        return 0.0


def reasoning_score(example, pred, trace=None) -> float:
    """Score the reasoning quality based on mistakes and invalid responses."""
    try:
        mistakes = getattr(pred, "mistakes", 0)
        invalid_responses = getattr(pred, "invalid_responses", 0)

        total_errors = mistakes + invalid_responses
        return max(0.0, 1.0 - total_errors * 0.25)

    except Exception:
        return 0.0


def efficiency_score(example, pred, trace=None) -> float:
    """Score based on efficiency (fewer attempts is better)."""
    try:
        attempts = getattr(pred, "attempts", 6)
        success = getattr(pred, "success", False)

        if not success:
            return 0.0

        # Perfect score for 4 attempts (minimum possible), decreasing from there
        max_attempts = 6
        if attempts <= 4:
            return 1.0
        else:
            return max(0.0, 1.0 - (attempts - 4) / (max_attempts - 4))

    except Exception:
        return 0.0


def overall_quality(example, pred, trace=None) -> float:
    """Overall quality score combining all factors."""
    try:
        success = getattr(pred, "success", False)
        groups_solved = getattr(pred, "groups_solved", 0)
        attempts = getattr(pred, "attempts", 0)

        success_rate = 1.0 if success else 0.0
        strategy = strategy_score(example, pred, trace)
        efficiency = efficiency_score(example, pred, trace)
        reasoning = reasoning_score(example, pred, trace)

        if success:
            return (
                0.4 * success_rate + 0.3 * strategy + 0.2 * efficiency + 0.1 * reasoning
            )
        else:
            # For failed attempts, focus on partial progress
            max_attempts = 6
            return (
                0.5 * (groups_solved / 4.0)
                + 0.3 * reasoning
                + 0.2 * min(attempts / max_attempts, 1.0)
            )

    except Exception:
        return 0.0


def partial_credit_score(example, pred, trace=None) -> float:
    """Score based on groups solved, even if puzzle wasn't completed."""
    try:
        groups_solved = getattr(pred, "groups_solved", 0)
        return groups_solved / 4.0  # Score from 0.0 to 1.0

    except Exception:
        return 0.0


# start_detailed_puzzle_analysis
def detailed_puzzle_analysis(results) -> Dict[str, Any]:
    """Analyze puzzle solving results for patterns and insights."""
    if not results:
        return {"error": "No results provided"}

    total_puzzles = len(results)
    successful_puzzles = sum(1 for r in results if r.get("success", False))

    # Analyze by difficulty if available
    difficulty_analysis = {
        "easy": {"attempted": 0, "solved": 0},
        "medium": {"attempted": 0, "solved": 0},
        "hard": {"attempted": 0, "solved": 0},
    }

    # Calculate average metrics
    avg_attempts = sum(r.get("attempts", 0) for r in results) / total_puzzles
    avg_mistakes = sum(r.get("mistakes", 0) for r in results) / total_puzzles

    return {
        "total_puzzles": total_puzzles,
        "success_rate": successful_puzzles / total_puzzles,
        "avg_attempts": avg_attempts,
        "avg_mistakes": avg_mistakes,
        "difficulty_breakdown": difficulty_analysis,
    }


# end_detailed_puzzle_analysis


# Main evaluation function matching DSPy patterns
# start_success_metric
def success_metric(example, pred, trace=None) -> bool:
    """Main metric function for DSPy evaluation - returns boolean like the provided example."""
    if not hasattr(pred, "success"):
        return False
    return pred.success


# end_success_metric
