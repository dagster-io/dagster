import {useMemo} from 'react';

import {useStartTrace} from '../performance';

export const useRunRootTrace = () => {
  const trace = useStartTrace('RunRoot');
  return useMemo(() => {
    let logsLoaded = false;
    let runsLoaded = false;
    function onLoaded() {
      if (logsLoaded && runsLoaded) {
        trace.endTrace();
      }
    }
    return {
      onLogsLoaded() {
        logsLoaded = true;
        onLoaded();
      },
      onRunLoaded() {
        runsLoaded = true;
        onLoaded();
      },
    };
  }, [trace]);
};

export type RunRootTrace = ReturnType<typeof useRunRootTrace>;
