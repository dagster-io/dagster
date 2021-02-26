import * as React from 'react';

import {featureEnabled, FeatureFlag} from 'src/app/Util';
import {LeftNav} from 'src/nav/LeftNav';
import {LeftNavSimple} from 'src/nav/LeftNavSimple';

export const LeftNavBranch = () => {
  const isFlagged = featureEnabled(FeatureFlag.LeftNav);
  return isFlagged ? <LeftNavSimple /> : <LeftNav />;
};
