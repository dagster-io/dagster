import {Checkbox} from '@blueprintjs/core';
import * as React from 'react';

import {useDocumentTitle} from '../hooks/useDocumentTitle';

import {FeatureFlag, getFeatureFlags, setFeatureFlags} from './Flags';

export const FeatureFlagsRoot = () => {
  const [flags, setFlags] = React.useState<FeatureFlag[]>(() => getFeatureFlags());

  React.useEffect(() => {
    setFeatureFlags(flags);
  });

  useDocumentTitle('Feature Flags');

  const toggleFlag = (flag: FeatureFlag) => {
    setFlags(flags.includes(flag) ? flags.filter((f) => f !== flag) : [...flags, flag]);
  };

  return (
    <div style={{padding: 30, paddingTop: 0}}>
      <h4>Experimental Features</h4>
      <div>
        <Checkbox
          label={'Debug Console Logging'}
          checked={flags.includes(FeatureFlag.flagDebugConsoleLogging)}
          onChange={() => toggleFlag(FeatureFlag.flagDebugConsoleLogging)}
        />
      </div>
      <div>
        <Checkbox
          label={'Experimental Core APIs (Job & Graph)'}
          checked={flags.includes(FeatureFlag.flagPipelineModeTuples)}
          onChange={() => toggleFlag(FeatureFlag.flagPipelineModeTuples)}
        />
      </div>
    </div>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default FeatureFlagsRoot;
