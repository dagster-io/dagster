import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {ButtonWIP as Button} from './Button';
import {Group} from './Group';
import {IconWIP as Icon} from './Icon';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Button',
  component: Button,
} as Meta;

export const Default = () => {
  return (
    <Group direction="column" spacing={8}>
      <Button>Button</Button>
      <Button icon={<Icon name="star" />}>Button</Button>
      <Button rightIcon={<Icon name="close" />}>Button</Button>
      <Button icon={<Icon name="source" />} rightIcon={<Icon name="expand_more" />}>
        Button
      </Button>
      <Button icon={<Icon name="cached" />} />
    </Group>
  );
};

export const Intent = () => {
  return (
    <Group direction="column" spacing={8}>
      <Button icon={<Icon name="star" />}>No intent set</Button>
      <Button icon={<Icon name="star" />} intent="primary">
        Primary
      </Button>
      <Button icon={<Icon name="done" />} intent="success">
        Success
      </Button>
      <Button icon={<Icon name="error" />} intent="danger">
        Danger
      </Button>
      <Button icon={<Icon name="warning" />} intent="warning">
        Warning
      </Button>
      <Button icon={<Icon name="star" />} intent="none">
        None
      </Button>
    </Group>
  );
};

export const Disabled = () => {
  return (
    <Group direction="column" spacing={8}>
      <Button icon={<Icon name="star" />} intent="primary">
        Enabled
      </Button>
      <Button icon={<Icon name="cached" />} disabled intent="primary">
        Disabled
      </Button>
    </Group>
  );
};
