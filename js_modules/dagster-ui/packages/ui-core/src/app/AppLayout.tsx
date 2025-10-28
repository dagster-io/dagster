import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

import {AppTopNav} from './AppTopNav/AppTopNav';
import {AppWithNewLayout} from './AppWithNewLayout';
import {AppWithOldLayout} from './AppWithOldLayout';
import {featureEnabled} from './Flags';
import {HelpMenu} from './HelpMenu';
import {UserSettingsButton} from './UserSettingsButton';

interface Props {
  children: React.ReactNode;
}
export const AppLayout = ({children}: Props) => {
  const newLayout = featureEnabled(FeatureFlag.flagNavigationUpdate);
  if (newLayout) {
    return <AppWithNewLayout>{children}</AppWithNewLayout>;
  }

  return (
    <AppWithOldLayout
      top={
        <AppTopNav allowGlobalReload>
          <HelpMenu showContactSales={false} />
          <UserSettingsButton />
        </AppTopNav>
      }
    >
      {children}
    </AppWithOldLayout>
  );
};
