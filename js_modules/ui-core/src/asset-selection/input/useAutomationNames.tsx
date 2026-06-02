import {useMemo} from 'react';

import {COMMON_COLLATOR} from '../../app/Util';
import {useAutomations} from '../../automation/useAutomations';

/**
 * Extracts sorted sensor and schedule names from the workspace context.
 * Used by autocomplete providers to populate sensor: and schedule: suggestions.
 */
export function useAutomationNames() {
  const {automations} = useAutomations();

  const sensorNames = useMemo(
    () =>
      automations
        .filter((a) => a.type === 'sensor')
        .map((a) => a.name)
        .sort((a, b) => COMMON_COLLATOR.compare(a, b)),
    [automations],
  );

  const scheduleNames = useMemo(
    () =>
      automations
        .filter((a) => a.type === 'schedule')
        .map((a) => a.name)
        .sort((a, b) => COMMON_COLLATOR.compare(a, b)),
    [automations],
  );

  return {sensorNames, scheduleNames};
}
