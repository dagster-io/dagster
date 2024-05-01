import {DependencyList, EffectCallback, useRef} from 'react';
/**
 * DO NOT CALL `setState` from within this effect or from any function called by this effect.
 * THIS IS NOT INTENDED TO TRIGGER REACT UPDATES.
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
