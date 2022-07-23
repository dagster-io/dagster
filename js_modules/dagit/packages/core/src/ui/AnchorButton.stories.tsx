import {ExternalAnchorButton, Group, Icon} from '@dagster-io/ui';
import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {AnchorButton} from './AnchorButton';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'AnchorButton',
  component: AnchorButton,
} as Meta;

export const Default = () => {
  return (
    <Group direction="column" spacing={8}>
      <AnchorButton to="/">Button</AnchorButton>
      <AnchorButton to="/" icon={<Icon name="star" />}>
        Button
      </AnchorButton>
      <AnchorButton to="/" rightIcon={<Icon name="close" />}>
        Button
      </AnchorButton>
      <AnchorButton to="/" icon={<Icon name="source" />} rightIcon={<Icon name="expand_more" />}>
        Button
      </AnchorButton>
      <AnchorButton to="/" icon={<Icon name="cached" />} />
    </Group>
  );
};

export const Intent = () => {
  return (
    <Group direction="column" spacing={8}>
      <AnchorButton to="/" icon={<Icon name="star" />}>
        No intent set
      </AnchorButton>
      <AnchorButton to="/" icon={<Icon name="star" />} intent="primary">
        Primary
      </AnchorButton>
      <AnchorButton to="/" icon={<Icon name="done" />} intent="success">
        Success
      </AnchorButton>
      <AnchorButton to="/" icon={<Icon name="error" />} intent="danger">
        Danger
      </AnchorButton>
      <AnchorButton to="/" icon={<Icon name="warning" />} intent="warning">
        Warning
      </AnchorButton>
      <AnchorButton to="/" icon={<Icon name="star" />} intent="none">
        None
      </AnchorButton>
    </Group>
  );
};

export const Outlined = () => {
  return (
    <Group direction="column" spacing={8}>
      <AnchorButton to="/" outlined icon={<Icon name="star" />}>
        No intent set
      </AnchorButton>
      <AnchorButton to="/" outlined icon={<Icon name="star" />} intent="primary">
        Primary
      </AnchorButton>
      <AnchorButton to="/" outlined icon={<Icon name="done" />} intent="success">
        Success
      </AnchorButton>
      <AnchorButton to="/" outlined icon={<Icon name="error" />} intent="danger">
        Danger
      </AnchorButton>
      <AnchorButton to="/" outlined icon={<Icon name="warning" />} intent="warning">
        Warning
      </AnchorButton>
      <AnchorButton to="/" outlined icon={<Icon name="star" />} intent="none">
        None
      </AnchorButton>
    </Group>
  );
};

export const ExternalButton = () => {
  return (
    <Group direction="column" spacing={8}>
      <ExternalAnchorButton href="https://html5zombo.com/">Button</ExternalAnchorButton>
      <ExternalAnchorButton href="https://html5zombo.com/" icon={<Icon name="star" />}>
        Button
      </ExternalAnchorButton>
      <ExternalAnchorButton href="https://html5zombo.com/" rightIcon={<Icon name="close" />}>
        Button
      </ExternalAnchorButton>
      <ExternalAnchorButton
        href="https://html5zombo.com/"
        icon={<Icon name="source" />}
        rightIcon={<Icon name="expand_more" />}
      >
        Button
      </ExternalAnchorButton>
      <ExternalAnchorButton href="https://html5zombo.com/" icon={<Icon name="cached" />} />
    </Group>
  );
};
