import {Story, Meta} from '@storybook/react';
import * as React from 'react';

import {TimeElapsed, Props} from '../TimeElapsed';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'TimeElapsed',
  component: TimeElapsed,
} as Meta;

const Template: Story<Props> = (props) => <TimeElapsed {...props} />;

const now = Date.now() / 1000;
const startUnix = now - 60;

export const Completed = Template.bind({});
Completed.args = {
  startUnix,
  endUnix: now,
};

export const Running = Template.bind({});
Running.args = {
  startUnix,
};

export const LongRunning = Template.bind({});
LongRunning.args = {
  startUnix: now - 60 * 60 * 1.5,
};
