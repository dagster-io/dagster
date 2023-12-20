import React from 'react';

import {useStartTrace} from '../performance';

export const useRunRootTrace = () => {
  const trace = useStartTrace('RunRoot');
  return React.useMemo(() => {
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
