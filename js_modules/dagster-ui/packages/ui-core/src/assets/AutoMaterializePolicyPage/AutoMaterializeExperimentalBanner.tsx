import {Alert, Box, Colors, Icon, Popover, Tag} from '@dagster-io/ui-components';
import React from 'react';
import styled from 'styled-components';

const AutoMaterializeExperimentalText = (
  <span>
    You can learn more about this new feature and provide feedback{' '}
    <a href="https://docs.dagster.io/concepts/assets/asset-auto-execution#auto-materializing-assets-">
      here
    </a>
    .
  </span>
);

export const AutoMaterializeExperimentalBanner = () => {
  return (
    <Alert
      intent="info"
      title="Auto-materialize policies are experimental"
      icon={<Icon name="info" color={Colors.Blue700} />}
      description={AutoMaterializeExperimentalText}
    />
  );
};

export const AutoMaterializeExperimentalTag = () => {
  return (
    <Popover
      content={<Container>{AutoMaterializeExperimentalText}</Container>}
      hoverOpenDelay={100}
      hoverCloseDelay={100}
      placement="top"
      interactionKind="hover"
    >
      <Tag intent="primary">Experimental</Tag>
    </Popover>
  );
};

const Container = styled(Box)`
  border-radius: 8px;
  overflow: hidden;
  background: ${Colors.Dark};
  padding: 8px 12px;
  color: ${Colors.Gray100};

  & a {
    color: ${Colors.White};
    text-decoration: underline;
  }
`;
