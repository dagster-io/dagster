import {Props, TimeElapsed} from '../TimeElapsed';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'TimeElapsed',
  component: TimeElapsed,
};

const Template = (props: Props) => <TimeElapsed {...props} />;

const now = Date.now() / 1000;
const startUnix = now - 60;

const SECOND = 1;
const MINUTE = 60 * SECOND;
const HOUR = 60 * MINUTE;

export const Completed = {
  render: (args: Props) => <Template {...args} />,
  args: {
    startUnix,
    endUnix: now,
  },
};

export const Running = {
  render: (args: Props) => <Template {...args} />,
  args: {
    startUnix,
  },
};

export const LongRunning = {
  render: (args: Props) => <Template {...args} />,
  args: {
    startUnix: now - 60 * 60 * 1.5,
  },
};

export const HoursMinuteSecondsMsec = {
  render: (args: Props) => <Template {...args} />,
  args: {
    startUnix: 1,
    endUnix: 1 + HOUR + MINUTE + SECOND + 0.069,
    showMsec: true,
  },
};

export const HoursSecondsMsec = {
  render: (args: Props) => <Template {...args} />,
  args: {
    startUnix: 1,
    endUnix: 1 + HOUR + SECOND + 0.069,
    showMsec: true,
  },
};

export const HoursMsec = {
  render: (args: Props) => <Template {...args} />,
  args: {
    startUnix: 1,
    endUnix: 1 + HOUR + 0.069,
    showMsec: true,
  },
};

export const MinutesMsec = {
  render: (args: Props) => <Template {...args} />,
  args: {
    startUnix: 1,
    endUnix: 1 + MINUTE + 0.069,
    showMsec: true,
  },
};

export const SecMsec = {
  render: (args: Props) => <Template {...args} />,
  args: {
    startUnix: 1,
    endUnix: 1 + SECOND + 0.069,
    showMsec: true,
  },
};

export const Msec = {
  render: (args: Props) => <Template {...args} />,
  args: {
    startUnix: 1,
    endUnix: 1 + 0.069,
    showMsec: true,
  },
};
