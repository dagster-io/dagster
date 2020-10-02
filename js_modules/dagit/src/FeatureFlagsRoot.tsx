import * as React from 'react';

import {getFeatureFlags, setFeatureFlags, FeatureFlag} from 'src/Util';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';

export const FeatureFlagsRoot = () => {
  const [flags, setFlags] = React.useState<FeatureFlag[]>(getFeatureFlags());

  React.useEffect(() => {
    setFeatureFlags(flags);
  });

  useDocumentTitle('Feature Flags');

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const toggleFlag = (flag: FeatureFlag) => {
    setFlags(flags.includes(flag) ? flags.filter((f) => f !== flag) : [...flags, flag]);
  };

  return (
    <div style={{padding: 30, paddingTop: 0}}>
      <h4>Experimental Features</h4>
      <div>
        {/* <Checkbox
          label={"Gaant-style Execution Plan"}
          checked={flags.includes(FeatureFlag.GaantExecutionPlan)}
          onChange={() => toggleFlag(FeatureFlag.GaantExecutionPlan)}
        /> */}
        There are no experimental features at this time.
      </div>
    </div>
  );
};
