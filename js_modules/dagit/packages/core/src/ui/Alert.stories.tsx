import {Story, Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {Alert, Props} from './Alert';
import {ButtonLink} from './ButtonLink';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Alert',
  component: Alert,
} as Meta;

const Template: Story<Props> = (props) => <Alert {...props} />;

export const Example = Template.bind({});
Example.args = {
  intent: 'info',
  title: 'This pipeline run is queued.',
  description: (
    <div>
      Click <ButtonLink>here</ButtonLink> to proceed.
    </div>
  ),
};
