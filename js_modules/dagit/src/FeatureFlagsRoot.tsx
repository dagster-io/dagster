/* eslint-disable */
import * as React from 'react';
import {getFeatureFlags, setFeatureFlags, FeatureFlag} from './Util';
import {Checkbox} from '@blueprintjs/core';

export const FeatureFlagsRoot = () => {
  const [flags, setFlags] = React.useState<FeatureFlag[]>(getFeatureFlags());

  React.useEffect(() => {
    setFeatureFlags(flags);
  });

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
