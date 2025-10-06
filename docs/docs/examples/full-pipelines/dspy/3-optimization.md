---
title: Optimize the puzzle solver with MIPROv2
description: Automatically optimize the puzzle solver with MIPROv2
last_update:
  author: Dennis Hume
sidebar_position: 40
---

While our baseline Chain-of-Thought solver provides a solid foundation, [MIPROv2](https://dspy.ai/api/optimizers/MIPROv2/) takes it to the next level through automatic optimization. This sophisticated algorithm doesn't just use fixed prompts. It actively generates and tests different instruction variants, curates effective few-shot examples, and systematically improves the solver's performance through data-driven refinement.

## Optimization configuration

The optimization process requires careful tuning to balance performance gains against computational costs. Our configuration system provides granular control over the optimization algorithm's behavior:

<CodeExample
  path="docs_projects/project_dspy/config.py"
  language="python"
  startAfter="start_get_optimizer_config"
  endBefore="end_get_optimizer_config"
  title="config.py"
/>

These settings work together to create a robust optimization framework: MIPROv2 serves as our primary algorithm due to its superior performance on reasoning tasks, while the auto-mode setting controls optimization intensity. "Light" mode provides quick improvements suitable for development, while "heavy" mode runs exhaustive searches for production deployments.

The threshold settings prevent wasted computation. We only optimize models that show baseline competency (performance_threshold of 0.3), and we only accept changes that provide meaningful improvements (improvement_threshold of 0.05). This ensures our optimization cycles focus on models worth improving and changes worth deploying.

## Running optimization

The optimization process transforms our baseline solver into a highly tuned puzzle-solving specialist. This transformation happens automatically through MIPROv2's sophisticated search and refinement algorithms:

<CodeExample
  path="docs_projects/project_dspy/src/project_dspy/components/ds_py_model_builder.py"
  language="python"
  startAfter="start_optimized_model_asset"
  endBefore="end_optimized_model_asset"
  title="src/project_dspy/components/ds_py_model_builder.py"
/>

The magic happens in the `optimizer.compile()` call, where MIPROv2 takes our baseline solver and training puzzles, then systematically experiments with different approaches. It generates multiple instruction variants ("Find four words that share a common theme" vs "Identify the strongest semantic connection among these words"), tests various few-shot example combinations, and measures performance against our success metric.

The optimizer uses our training puzzles to understand what constitutes good puzzle-solving behavior, while our custom success metric ensures optimization focuses on actual puzzle completion rather than generic language model metrics. The result is a solver that has learned not just to reason about word relationships, but to do so in ways that consistently lead to successful puzzle solutions.

## Performance monitoring

Effective optimization requires intelligent guardrails to prevent wasted computational resources and ensure meaningful improvements. Our monitoring system implements several layers of quality control:

<CodeExample
  path="docs_projects/project_dspy/config.py"
  language="python"
  startAfter="start_dspy_performance_threshold"
  endBefore="end_dspy_performance_threshold"
  title="config.py"
/>

The performance threshold (0.3) acts as a quality gate. We only invest optimization resources in models that show basic puzzle-solving competency. This prevents the optimizer from trying to polish fundamentally flawed approaches and ensures our computational budget focuses on promising candidates.

The improvement threshold (0.05) guards against accepting marginal changes that could be due to random variation rather than genuine optimization. In puzzle-solving tasks, a 5% improvement in success rate represents meaningful progress. The difference between solving 3 out of 10 puzzles versus 3.5 out of 10. This threshold ensures our optimization cycles result in deployable improvements rather than statistical noise.

## Component integration

The optimization process is designed for real-world deployment scenarios where different environments may require different optimization strategies. The Dagster Component architecture makes this flexibility possible through configuration inheritance and override patterns:

<CodeExample
  path="docs_projects/project_dspy/src/project_dspy/components/connections_model_builder.py"
  language="python"
  startAfter="start_connections_init"
  endBefore="end_connections_init"
  title="src/project_dspy/components/connections_model_builder.py"
/>

This component pattern provides powerful flexibility: the base `DSPyModelBuilder` contains all the optimization logic and can be used for any DSPy project, while `ConnectionsModelBuilder` specializes it with puzzle-specific defaults. Development environments might use smaller evaluation subsets (30 puzzles) and lower performance thresholds for rapid iteration, while production deployments could use larger evaluation sets and stricter thresholds for robust models.

The configuration-driven approach means teams can maintain different optimization strategies for different use cases without duplicating code. A research team might prioritize optimization_enabled=True with heavy auto-mode for maximum performance, while a cost-conscious deployment might disable optimization and rely on carefully tuned baseline models.

## Next steps

With our optimized solver in hand, we need comprehensive evaluation to understand how much the optimization improved our puzzle-solving capabilities and whether the model is ready for production deployment.

- Continue this tutorial with [performance evaluation](/examples/full-pipelines/dspy/evaluation)
