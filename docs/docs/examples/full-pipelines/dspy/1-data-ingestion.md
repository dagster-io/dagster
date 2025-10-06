---
title: Ingest puzzle data
description: Load and prepare Connections puzzle data for AI training
last_update:
  author: Dennis Hume
sidebar_position: 20
---

[NYT Connections](https://www.nytimes.com/games/connections) is a word puzzle where players find four groups of four related words from a 16-word grid. Each group has a difficulty level: **Yellow** (easiest), **Green**, **Blue**, and **Purple** (hardest). Our DsPy solver needs structured data to learn effective puzzle-solving strategies.

## Data structure and loading

The foundation of our AI system starts with well-structured data classes that model the puzzle domain. These classes capture not just the raw puzzle data, but also the game state needed to track solving progress:

<CodeExample
  path="docs_projects/project_dspy/dspy_modules/puzzle.py"
  language="python"
  startAfter="start_puzzle_dataclasses"
  endBefore="end_puzzle_dataclasses"
  title="dspy_modules/puzzle.py"
/>

The `Puzzle` class serves as our core data structure, containing the 16 words and their correct group assignments with difficulty levels. The `GameState` class tracks the dynamic aspects of puzzle-solving: which groups have been solved, how many mistakes were made, and whether the game is complete. This separation allows our DSPy solver to reason about both the static puzzle structure and the evolving game dynamics.

The data loading process includes comprehensive validation to ensure puzzle integrity. Every puzzle must have exactly 16 words arranged in 4 groups of 4, with each group assigned one of the four difficulty colors. This validation prevents corrupted data from affecting model training and ensures consistent puzzle structure across the dataset.

## Creating training data

The data preparation process is handled by a Dagster asset that orchestrates the entire pipeline from raw CSV files to DSPy training examples. This approach ensures reproducible data splits and consistent preprocessing:

<CodeExample
  path="docs_projects/project_dspy/src/project_dspy/components/ds_py_model_builder.py"
  language="python"
  startAfter="start_puzzle_data_asset"
  endBefore="end_puzzle_data_asset"
  title="src/project_dspy/components/ds_py_model_builder.py"
/>

This asset performs several critical functions:

- It loads puzzles from the CSV file and validates their structure using our domain-specific validation logic.
- It splits the data into training and evaluation sets using a configurable ratio (default 25% for training), ensuring we have sufficient data for both optimization and testing.
- The asset also handles practical considerations, like taking a subset of puzzles for efficient evaluation during development, while maintaining the full dataset for comprehensive testing.

All operations are tracked with detailed metadata, providing visibility into dataset size, split ratios, and data quality metrics. This transparency is crucial for understanding model performance and debugging potential data issues.

## Component configuration

The data pipeline leverages [Dagster Components](/guides/build/components) to create reusable, configurable data processing workflows. This YAML configuration defines all the key parameters for the Connections puzzle solver:

<CodeExample
  path="docs_projects/project_dspy/src/project_dspy/defs/connections_model/defs.yaml"
  language="yaml"
  title="src/project_dspy/defs/connections_model/defs.yaml"
/>

This configuration encapsulates specific defaults optimized for Connections puzzles. The data path points to our puzzle CSV file, the performance threshold (0.3) represents a reasonable baseline success rate for puzzle-solving, and the train/test split (0.25) balances having enough training data with sufficient evaluation coverage.

The component approach provides several benefits:

- Configurations can be easily modified for different environments or puzzle variants.
- The same component can be deployed across development and production with different parameters.
- The declarative YAML format makes it easy to understand and version control the pipeline settings.

## Next steps

Now that we have a robust data ingestion pipeline that loads, validates, and prepares puzzle data for training, we can move on to building the core AI solver that will use this data to learn puzzle-solving strategies.

- Continue this tutorial with [building the DSPy solver](/examples/full-pipelines/dspy/dspy-modeling)
