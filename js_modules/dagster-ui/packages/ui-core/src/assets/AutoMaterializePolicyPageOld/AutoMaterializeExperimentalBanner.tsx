import {Alert, Icon, Tag, Tooltip, Colors} from '@dagster-io/ui-components';
import React from 'react';

const LearnMoreLink =
  'https://docs.dagster.io/concepts/assets/asset-auto-execution#auto-materializing-assets-';

export const AutoMaterializeExperimentalBanner = () => {
  return (
    <Alert
      intent="info"
      title="Auto-materialize policies are experimental"
      icon={<Icon name="info" color={Colors.accentBlue()} />}
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
