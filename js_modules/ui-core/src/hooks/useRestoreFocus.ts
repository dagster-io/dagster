import {useCallback, useRef} from 'react';

/** Tracks a dialog trigger and restores focus to it or a fallback. */
export const useRestoreFocus = (getFallbackFocusTarget: () => HTMLElement | null) => {
  const triggerRef = useRef<HTMLElement | null>(null);

  const rememberTrigger = useCallback((trigger: HTMLElement) => {
    triggerRef.current = trigger;
  }, []);

  const restoreFocus = useCallback(() => {
    const trigger = triggerRef.current;
    triggerRef.current = null;
    if (trigger === null) {
      return;
    }
    if (trigger.isConnected) {
      trigger.focus();
    }
    if (document.activeElement !== trigger) {
      getFallbackFocusTarget()?.focus();
    }
  }, [getFallbackFocusTarget]);

  return {rememberTrigger, restoreFocus};
};
