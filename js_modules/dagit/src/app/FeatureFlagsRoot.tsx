import {Checkbox} from '@blueprintjs/core';
import * as React from 'react';

import {getFeatureFlags, setFeatureFlags, FeatureFlag} from 'src/app/Util';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
export const FeatureFlagsRoot = () => {
  const [flags, setFlags] = React.useState<FeatureFlag[]>(getFeatureFlags());

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
          checked={flags.includes(FeatureFlag.DebugConsoleLogging)}
          onChange={() => toggleFlag(FeatureFlag.DebugConsoleLogging)}
        />
        <Checkbox
          label={'Directory-structured Asset Catalog'}
          checked={flags.includes(FeatureFlag.DirectoryAssetCatalog)}
          onChange={() => toggleFlag(FeatureFlag.DirectoryAssetCatalog)}
        />
      </div>
    </div>
  );
};
