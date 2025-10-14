import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

import {AppWithNewLayout} from './AppWithNewLayout';
import {AppWithOldLayout} from './AppWithOldLayout';
import {featureEnabled} from './Flags';

interface Props {
  children: React.ReactNode;
}
export const AppLayout = ({children}: Props) => {
  const newLayout = featureEnabled(FeatureFlag.flagNavigationUpdate);
  if (newLayout) {
    return <AppWithNewLayout>{children}</AppWithNewLayout>;
  }
  return <AppWithOldLayout>{children}</AppWithOldLayout>;
};
