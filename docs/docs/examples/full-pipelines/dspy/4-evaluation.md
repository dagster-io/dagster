---
title: Evaluate performance
description: Evaluate puzzle-solving performance and monitor model quality
last_update:
  author: Dennis Hume
sidebar_position: 50
---

Evaluation in puzzle-solving AI goes beyond simple accuracy metrics. We need to understand not just whether our solver can complete puzzles, but how efficiently it does so, what strategies it employs, and whether its performance is consistent across different puzzle difficulties. This comprehensive evaluation approach ensures our AI is truly ready for real-world deployment.

## Evaluation metrics

The evaluation system uses domain-specific metrics that capture the nuances of strategic puzzle-solving. Unlike generic language model metrics, these focus on game-specific performance characteristics:

<CodeExample
  path="docs_projects/project_dspy/dspy_modules/connections_metrics.py"
  language="python"
  startAfter="start_success_metric"
  endBefore="end_success_metric"
  title="dspy_modules/connections_metrics.py"
/>

The success metric serves as the foundation for DSPy's optimization algorithms. It provides the clear binary signal needed for the optimizer to distinguish between better and worse approaches. But this simple metric is complemented by sophisticated evaluation frameworks that measure strategy quality, efficiency, and consistency.

Consider the difference between two solvers that both achieve 70% success rates: one might consistently solve puzzles in 4-5 attempts with minimal mistakes, while another might require 6 attempts and make many errors before succeeding. Both are "successful" but represent very different levels of puzzle-solving competency. Our evaluation system captures these crucial distinctions.

## Model predictions

Every puzzle-solving session generates rich performance data that goes far beyond a simple pass/fail result. This detailed prediction structure enables comprehensive analysis of solver behavior and performance patterns:

<CodeExample
  path="docs_projects/project_dspy/dspy_modules/solver.py"
  language="python"
  startAfter="start_return_results"
  endBefore="end_return_results"
  title="dspy_modules/solver.py"
/>

This prediction structure tells a complete story of each puzzle-solving attempt. The metadata (puzzle ID, date) enables tracking performance across different puzzle sets and time periods. The success metrics capture the outcome, while the attempt counts reveal the efficiency of the solving strategy.

The timing data is particularly valuable for understanding solver behavior under different conditions. A solver that takes 30 seconds per puzzle might be suitable for offline analysis but problematic for real-time applications. The groups_solved count helps identify partial successes - a solver that consistently identifies 3 out of 4 groups is close to breakthrough performance and might benefit from different optimization strategies than one that struggles to find any groups.

## Production monitoring

Production deployment requires continuous monitoring to detect performance degradation, ensure quality maintenance, and trigger timely interventions. Our monitoring system provides automated oversight for the deployed solver:

<CodeExample
  path="docs_projects/project_dspy/config.py"
  language="python"
  startAfter="start_accuracy_alert_threshold"
  endBefore="end_accuracy_alert_threshold"
  title="config.py"
/>

The 65% accuracy alert threshold represents a carefully calibrated balance. It's high enough to catch meaningful performance degradation (a drop from 70% to 60% success rate would signal serious issues) while avoiding false alarms from normal statistical variation. In puzzle-solving applications, maintaining consistent performance is critical for user experience.

This monitoring approach enables proactive maintenance rather than reactive firefighting. When performance drops below the threshold, the system can automatically trigger re-optimization using fresh data, potentially incorporating new puzzle patterns or addressing concept drift in the underlying language model capabilities.

## Deployment criteria

Moving from development to production requires systematic evaluation against well-defined quality gates. These criteria ensure deployed models meet both performance and operational requirements:

**Performance quality gates:**

- **Success rate > 60%**: This threshold represents meaningful puzzle-solving capability - roughly 6 out of 10 puzzles solved correctly
- **Optimization improvement > 5%**: Ensures optimization efforts produce meaningful gains, not just statistical noise
- **Better than random > 25%**: Random guessing would solve ~25% of puzzles by chance; our solver must demonstrate genuine reasoning
- **Resource efficiency**: Response times under 30 seconds per puzzle, API costs within budget constraints

**Operational readiness indicators:**

- Consistent performance across different puzzle difficulty levels (yellow, green, blue, purple groups)
- Stable performance over time without significant degradation
- Robust error handling for malformed inputs or API failures
- Comprehensive logging and monitoring integration

## Dagster Components benefits

This Connections solver exemplifies the power of combining DSPy's AI capabilities with Dagster's production orchestration. The resulting architecture demonstrates several key advantages for building reliable AI systems:

**Reusability and standardization**: The `ConnectionsModelBuilder` component encapsulates puzzle-solving expertise in a reusable package. Teams can deploy this component across development, staging, and production environments with environment-specific configurations, ensuring consistent behavior while allowing for operational flexibility.

**Complete observability**: Every step from data ingestion through model optimization to performance evaluation is tracked and logged. This end-to-end visibility enables debugging performance issues, understanding model behavior, and maintaining audit trails for compliance requirements.

**Production-ready operations**: Built-in monitoring detects performance degradation, automated quality gates prevent deployment of underperforming models, and systematic evaluation ensures only models meeting strict criteria reach production. This operational rigor transforms experimental AI code into production-grade systems.

**Scalable architecture**: The component-based design supports scaling from individual research projects to enterprise-wide AI platforms. The same optimization and evaluation patterns can be applied to different puzzle types, game domains, or entirely different AI applications.

This architecture provides a proven blueprint for building sophisticated AI applications that combine the cutting-edge capabilities of modern language models with the operational discipline required for production deployment. The result is AI systems that are not just intelligent, but reliable, maintainable, and ready for real-world use.
