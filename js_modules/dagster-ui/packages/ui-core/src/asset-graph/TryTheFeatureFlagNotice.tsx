import {
  Body,
  Box,
  Button,
  Subtitle1,
  colorAccentBlue,
  colorBackgroundBlue,
  colorTextLight,
} from '@dagster-io/ui-components';
import uniq from 'lodash/uniq';
import React from 'react';
import styled from 'styled-components';

import {FeatureFlag, getFeatureFlags, setFeatureFlags} from '../app/Flags';
import {useStateWithStorage} from '../hooks/useStateWithStorage';

const TITLE = 'Try the new asset graph';

const MESSAGE =
  "We're building a better asset graph experience with faster rendering, a new sidebar, collapsible groups, and more. You can opt-in to this experimental feature at any time from user settings.";

export const TryTheFeatureFlagNotice = () => {
  const [dismissed, setDismissed] = useStateWithStorage<boolean>(
    'new-graph-feature-flag',
    (val) => !!val,
  );

  if (dismissed) {
    return <span />;
  }
  return (
    <Container>
      <Box flex={{direction: 'column', gap: 4}}>
        <Subtitle1>{TITLE}</Subtitle1>
        <Body color={colorTextLight()}>{MESSAGE}</Body>
        <Box flex={{gap: 8}} margin={{top: 12}}>
          <Button
            intent="primary"
            onClick={() => {
              setFeatureFlags(uniq([...getFeatureFlags(), FeatureFlag.flagDAGSidebar]));
              window.location.reload();
            }}
          >
            Try it now
          </Button>
          <Button onClick={() => setDismissed(true)}>No thanks</Button>
        </Box>
      </Box>
    </Container>
  );
};

const Container = styled.div`
  position: absolute;
  left: 16px;
  bottom: 16px;
  z-index: 2;
  width: 700px;
  max-width: 50vw;
  border: 1px solid ${colorAccentBlue()};
  border-radius: 16px;
  background: ${colorBackgroundBlue()};
  padding: 24px;
`;
