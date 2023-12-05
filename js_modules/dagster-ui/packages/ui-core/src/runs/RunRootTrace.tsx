import React from 'react';

import {useStartTrace} from '../performance';

export const useRunRootTrace = () => {
  const logsLoaded = React.useRef(false);
  const runsLoaded = React.useRef(false);

  const trace = useStartTrace('RunRoot');
  const onLoaded = React.useCallback(() => {
    if (logsLoaded.current && runsLoaded.current) {
      trace.endTrace();
    }
  }, [trace]);
  return React.useMemo(
    () => ({
      onLogsLoaded() {
        logsLoaded.current = true;
        onLoaded();
      },
      onRunLoaded() {
        runsLoaded.current = true;
        onLoaded();
      },
    }),
    [],
  );
};
