---
title: Build the DSPy solver
description: Create a DSPy module for solving Connections puzzles
last_update:
  author: Dennis Hume
sidebar_position: 30
---

The DSPy solver transforms puzzle-solving from rule-based logic into learned reasoning patterns. By using [Chain-of-Thought](https://arxiv.org/abs/2201.11903) prompting, our AI learns to analyze word relationships, consider context clues, and develop strategic approaches that improve with training data.

## Solver module structure

The `ConnectionsSolver` module represents the core intelligence of our system. Rather than hard-coding puzzle-solving rules, it uses [DSPy's Chain-of-Thought framework](https://DSPy.ai/api/modules/ChainOfThought/) to enable the language model to reason through puzzles step-by-step:

<CodeExample
  path="docs_projects/project_dspy/dspy_modules/solver.py"
  language="python"
  startAfter="start_connections_solver"
  endBefore="end_connections_solver"
  title="dspy_modules/solver.py"
/>

A single Chain-of-Thought predictor takes structured inputs (game rules, available words, guess history, and attempt number) and outputs reasoned guesses. This signature defines the "contract" between the language model and our puzzle domain.

The integration with `ConnectionsGameLogic` is crucial. While the AI handles reasoning and pattern recognition, the game logic enforces rules, validates guesses, and provides structured feedback. This separation allows the AI to focus on what it does best (understanding relationships between words) while ensuring game mechanics remain consistent and reliable.

## Puzzle-solving loop

The heart of our solver is an iterative reasoning loop that mimics how a human might approach these puzzles. The solver makes educated guesses, learning from feedback, and refining strategy based on previous attempts:

<CodeExample
  path="docs_projects/project_dspy/dspy_modules/solver.py"
  language="python"
  startAfter="start_solving_loop"
  endBefore="end_solving_loop"
  title="dspy_modules/solver.py"
/>

This loop demonstrates the power of structured AI reasoning. In each iteration, the solver receives a complete picture of the current game state: which words are still available, what previous guesses were made and their outcomes, and which attempt this represents. The Chain-of-Thought predictor uses this rich context to generate not just a guess, but the reasoning behind it.

The feedback mechanism is critical for learning. When the solver makes a guess like "PARIS, LONDON, MADRID, ROME" for a capitals group, it receives immediate feedback: "CORRECT" if right, "INCORRECT" with remaining guesses if wrong, or "INVALID_RESPONSE" with detailed error information if the guess is malformed. This feedback becomes part of the context for subsequent guesses, allowing the AI to learn from mistakes within a single puzzle.

## Model deployment

The transition from development to production requires careful orchestration of model creation, configuration, and evaluation. Our Dagster component handles this complexity through well-defined assets that manage the entire model lifecycle:

<CodeExample
  path="docs_projects/project_dspy/src/project_dspy/components/ds_py_model_builder.py"
  language="python"
  startAfter="start_baseline_core"
  endBefore="end_baseline_core"
  title="src/project_dspy/components/ds_py_model_builder.py"
/>

This deployment pattern follows software engineering best practices:

- The DSPy resource ensures consistent language model configuration across all environments.
- The solver instance is created with a clean state for reproducible results.
- The model is immediately persisted to disk for reliable retrieval during optimization and evaluation phases.

The baseline model serves as our performance benchmark. Before we apply any optimization techniques, we need to understand how well the "vanilla" Chain-of-Thought approach performs. This baseline becomes crucial for measuring the effectiveness of subsequent optimizations and ensuring that our improvements are meaningful rather than just random variation.

## Next steps

- Continue this tutorial with [MIPROv2 optimization](/examples/full-pipelines/dspy/optimization)
