import {DependencyList, EffectCallback, useRef} from 'react';
/**
 * Beware, do not use this to run any effects that cause React updates.
 * This is intended for telemetry and even then this is not Suspense safe
 * because it mutates refs during render and Suspense blows away all component state (including refs).
 * Use with extreme care.
 */

export function useDangerousRenderEffect(effect: EffectCallback, deps: DependencyList) {
  const initialRender = useRef(true);
  const depsRef = useRef(deps);

  const dependenciesChanged = deps.some((dep, index) => dep !== depsRef.current[index]);

  // Run effect if it's the first render or if dependencies have changed
  if (initialRender.current || dependenciesChanged) {
    depsRef.current = deps;
    initialRender.current = false;
    effect();
  }
}
