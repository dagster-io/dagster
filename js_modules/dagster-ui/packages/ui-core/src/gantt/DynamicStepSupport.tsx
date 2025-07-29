/**
 * Ops with dynamic outputs yield execution plans like step_a => step_b[?] => step_c[?],
 * where the index syntax indicates that step_b and step_c may be invoked an arbitrary number
 * of times. At runtime, the Dagster UI replaces and duplicates these "planned dynamic steps" as it
 * observes invocations in the logs.
 *
 * Dagster UI currently parses step keys to implement this behavior and assumes that:
 *  - [?] Indicates a planned dynamic step
 *  - [ and ] are only used in dynamic steps
 *  - Index values are arbitrary (eg: step[1] or step[A] or step[US-East-1])
 *  - Index values are propagated through the entire subgraph after a dynamic invocation
 */
export function isDynamicStep(stepKey: string) {
  return stepKey.endsWith(']');
}

export function isPlannedDynamicStep(stepKey: string) {
  return stepKey.endsWith('[?]');
}

export function invocationsOfPlannedDynamicStep(plannedStepKey: string, runtimeStepKeys: string[]) {
  return runtimeStepKeys.filter((k) => k.startsWith(plannedStepKey.replace('?]', '')));
}

export function dynamicKeyWithoutIndex(stepKey: string) {
  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  return stepKey.split('[')[0]!;
}

export function replacePlannedIndex(stepKey: string, stepKeyWithIndex: string) {
  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  return stepKey.replace('[?]', stepKeyWithIndex.match(/(\[.*\])/)![1]!);
}
