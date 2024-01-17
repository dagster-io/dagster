import {Alert, Box, Icon, Tag, Tooltip, colorAccentBlue} from '@dagster-io/ui-components';
import React from 'react';

import {useStateWithStorage} from '../../hooks/useStateWithStorage';

const LearnMoreLink =
  'https://docs.dagster.io/concepts/assets/asset-auto-execution#auto-materializing-assets-';

export const AutoMaterializeExperimentalBanner = () => {
  const [closed, setClosed] = useStateWithStorage('automation-experimental', (value) => !!value);
  if (closed) {
    return null;
  }
  return (
    <Box padding={{horizontal: 24, vertical: 12}} border="bottom">
      <Alert
        intent="info"
        title="Automation policies are experimental"
        icon={<Icon name="info" color={colorAccentBlue()} />}
        onClose={() => {
          setClosed(true);
        }}
        description={
          <span>
            You can learn more about this new feature and provide feedback{' '}
            <a target="_blank" href={LearnMoreLink} rel="noreferrer">
              here
            </a>
            .
          </span>
        }
      />
    </Box>
  );
};

export const AutoMaterializeExperimentalTag = () => {
  return (
    <Tooltip content="Click to learn more about this new feature and provide feedback">
      <a target="_blank" href={LearnMoreLink} rel="noreferrer">
        <Tag intent="primary">Experimental</Tag>
      </a>
    </Tooltip>
  );
};
