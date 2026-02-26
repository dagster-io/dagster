import {DependencyList, EffectCallback, useMemo} from 'react';
/**
 * DO NOT CALL `setState` from within this effect or from any function called by this effect.
 * THIS IS NOT INTENDED TO TRIGGER REACT UPDATES.
 * This is intended for telemetry and even then this is not Suspense safe
 * because it mutates refs during render and Suspense blows away all component state (including refs).
 * Use with extreme care.
 */

export function useDangerousRenderEffect(effect: EffectCallback, deps: DependencyList) {
  useMemo(() => {
    effect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
}
