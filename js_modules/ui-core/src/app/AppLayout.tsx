import {useFullScreen} from './AppTopNav/AppTopNavContext';
import {useJobStateForNav} from './AppTopNav/useJobStateForNav';
import {isKioskMode} from './kioskMode';
import {MobileLayout} from './mobile/MobileLayout';
import {AppContainer} from './navigation/AppContainer';
import {NavCollapseProvider, useIsSmallScreen} from './navigation/NavCollapseProvider';
import {getBottomGroups, getTopGroups} from './navigation/mainNavigationItems';
import {useFeatureFlags} from './useFeatureFlags';

interface Props {
  banner?: React.ReactNode;
  children: React.ReactNode;
}

export const AppLayout = ({banner, children}: Props) => {
  const featureFlags = useFeatureFlags();
  const {isFullScreen} = useFullScreen();
  const jobState = useJobStateForNav();

  const topGroups = getTopGroups({featureFlags, jobState});
  const bottomGroups = getBottomGroups({featureFlags, jobState});
  const isSmallScreen = useIsSmallScreen();

  if (isSmallScreen) {
    return <MobileLayout>{children}</MobileLayout>;
  }

  return (
    <NavCollapseProvider>
      <AppContainer
        topGroups={topGroups}
        bottomGroups={bottomGroups}
        banner={banner}
        isFullScreenEnabled={isFullScreen || isKioskMode}
      >
        {children}
      </AppContainer>
    </NavCollapseProvider>
  );
};
