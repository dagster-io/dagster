import * as React from 'react';
import {Meta, Story} from '@storybook/react';

import {Props, TimeElapsed} from '../TimeElapsed';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'TimeElapsed',
  component: TimeElapsed,
} as Meta;

const Template: Story<Props> = (props) => <TimeElapsed {...props} />;

const now = Date.now() / 1000;
const startUnix = now - 60;

const SECOND = 1;
const MINUTE = 60 * SECOND;
const HOUR = 60 * MINUTE;

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

export const HoursMinuteSecondsMsec = Template.bind({});
HoursMinuteSecondsMsec.args = {
  startUnix: 1,
  endUnix: 1 + HOUR + MINUTE + SECOND + 0.069,
  showMsec: true,
};

export const HoursSecondsMsec = Template.bind({});
HoursSecondsMsec.args = {
  startUnix: 1,
  endUnix: 1 + HOUR + SECOND + 0.069,
  showMsec: true,
};

export const HoursMsec = Template.bind({});
HoursMsec.args = {
  startUnix: 1,
  endUnix: 1 + HOUR + 0.069,
  showMsec: true,
};

export const MinutesMsec = Template.bind({});
MinutesMsec.args = {
  startUnix: 1,
  endUnix: 1 + MINUTE + 0.069,
  showMsec: true,
};
export const SecMsec = Template.bind({});
SecMsec.args = {
  startUnix: 1,
  endUnix: 1 + SECOND + 0.069,
  showMsec: true,
};

export const Msec = Template.bind({});
Msec.args = {
  startUnix: 1,
  endUnix: 1 + 0.069,
  showMsec: true,
};
