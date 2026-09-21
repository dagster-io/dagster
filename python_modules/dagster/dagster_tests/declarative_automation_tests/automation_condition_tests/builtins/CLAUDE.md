# Automation Condition Builtin Tests

New tests should use `dg.evaluate_automation_conditions()` with `DagsterInstance.ephemeral()`. The async `AutomationConditionScenarioState` pattern is legacy.
