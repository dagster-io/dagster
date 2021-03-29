import * as React from 'react';

import {featureEnabled, FeatureFlag} from '../app/Util';

import {LeftNav} from './LeftNav';
import {LeftNavSimple} from './LeftNavSimple';

export const LeftNavBranch = () => {
  const isFlagged = featureEnabled(FeatureFlag.LeftNav);
  return isFlagged ? <LeftNavSimple /> : <LeftNav />;
};
