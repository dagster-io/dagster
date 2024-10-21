import {Alert, Box, ButtonLink} from '@dagster-io/ui-components';
import * as React from 'react';
import {useState} from 'react';
import {FeatureFlag} from 'shared/app/FeatureFlags.oss';
import styled from 'styled-components';

import {getFeatureFlags, setFeatureFlags, useFeatureFlags} from './Flags';
import {LayoutContext} from './LayoutProvider';
import {useStateWithStorage} from '../hooks/useStateWithStorage';
import {LEFT_NAV_WIDTH, LeftNav} from '../nav/LeftNav';

interface Props {
  banner?: React.ReactNode;
  children: React.ReactNode;
}

export const App = ({banner, children}: Props) => {
  const {nav} = React.useContext(LayoutContext);

  // todo dish: Remove flag and alert once this change has shipped.
  const {flagLegacyNav} = useFeatureFlags();
  const [didDismissNavAlert, setDidDismissNavAlert] = useStateWithStorage<boolean>(
    'new_navigation_alert',
    (json) => !!json,
  );

  const onClickMain = React.useCallback(() => {
    if (nav.isSmallScreen) {
      nav.close();
    }
  }, [nav]);

  return (
    <Container>
      <LeftNav />
      <Main $smallScreen={nav.isSmallScreen} $navOpen={nav.isOpen} onClick={onClickMain}>
        <div>{banner}</div>
        {!flagLegacyNav && !didDismissNavAlert ? (
          <ExperimentalNavAlert setDidDismissNavAlert={setDidDismissNavAlert} />
        ) : null}
        <ChildContainer>{children}</ChildContainer>
      </Main>
    </Container>
  );
};

interface AlertProps {
  setDidDismissNavAlert: (didDismissNavAlert: boolean) => void;
}

const ExperimentalNavAlert = (props: AlertProps) => {
  const {setDidDismissNavAlert} = props;
  const [flags] = useState<FeatureFlag[]>(() => getFeatureFlags());

  const revertToLegacyNavigation = () => {
    const copy = new Set(flags);
    copy.add(FeatureFlag.flagLegacyNav);
    setFeatureFlags(Array.from(copy));
    setDidDismissNavAlert(true);
    window.location.reload();
  };

  return (
    <Box padding={8} border="top-and-bottom">
      <Alert
        title={
          <>
            <span>Experimental navigation:</span>
            <span style={{fontWeight: 'normal'}}>
              {' '}
              We&apos;re testing some changes to make it easier to explore jobs and automations.{' '}
              <a
                href="https://github.com/dagster-io/dagster/discussions/21370"
                target="_blank"
                rel="noreferrer"
              >
                Share feedback
              </a>{' '}
              or{' '}
              <ButtonLink underline="always" onClick={revertToLegacyNavigation}>
                revert to legacy navigation
              </ButtonLink>
              .
            </span>
          </>
        }
        onClose={() => setDidDismissNavAlert(true)}
      />
    </Box>
  );
};

const Main = styled.div<{$smallScreen: boolean; $navOpen: boolean}>`
  height: 100%;
  z-index: 1;
  display: flex;
  flex-direction: column;

  ${({$navOpen, $smallScreen}) => {
    if ($smallScreen || !$navOpen) {
      return `
        margin-left: 0;
        width: 100%;
      `;
    }

    return `
      margin-left: ${LEFT_NAV_WIDTH}px;
      width: calc(100% - ${LEFT_NAV_WIDTH}px);
    `;
  }}
`;

const Container = styled.div`
  display: flex;
  height: calc(100% - 64px);
`;

const ChildContainer = styled.div`
  height: 100%;
  overflow: hidden;
`;
