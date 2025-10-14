import {TZDate} from '@date-fns/tz';
import {Meta} from '@storybook/nextjs';
import {endOfDay} from 'date-fns';
import memoize from 'lodash/memoize';
import {useState} from 'react';

import {Box} from '../Box';
import {DateRange, DayPickerWrapper} from '../DayPickerWrapper';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'DayPickerWrapper',
  component: DayPickerWrapper,
} as Meta<typeof DayPickerWrapper>;

const buildFormatter = memoize(
  (timeZone: string) =>
    new Intl.DateTimeFormat('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
      timeZone,
      timeZoneName: 'short',
      hour: 'numeric',
      minute: 'numeric',
      second: 'numeric',
    }),
);

export const Basic = () => {
  const [selected, setSelected] = useState<DateRange>({from: undefined, to: undefined});

  return (
    <Box padding={16}>
      <DayPickerWrapper
        mode="range"
        min={1}
        selected={selected}
        onSelect={setSelected}
        excludeDisabled
        required
        numberOfMonths={2}
      />
    </Box>
  );
};

export const WithTimeZone = () => {
  const [selected, setSelected] = useState<DateRange>({from: undefined, to: undefined});
  const formatter = buildFormatter('America/New_York');

  return (
    <Box padding={16}>
      <DayPickerWrapper
        mode="range"
        min={1}
        selected={selected}
        onSelect={setSelected}
        excludeDisabled
        required
        timeZone="America/New_York"
        numberOfMonths={2}
      />
      <Box padding={16}>
        <div>{selected.from ? formatter.format(selected.from) : 'No start date'}</div>
        <div>
          {selected.to
            ? formatter.format(endOfDay(new TZDate(selected.to, 'America/New_York')))
            : 'No end date'}
        </div>
      </Box>
    </Box>
  );
};

export const UnusualTimeZone = () => {
  const [selected, setSelected] = useState<DateRange>({from: undefined, to: undefined});
  const formatter = buildFormatter('Asia/Kolkata');

  return (
    <Box padding={16}>
      <DayPickerWrapper
        mode="range"
        min={1}
        selected={selected}
        onSelect={setSelected}
        excludeDisabled
        required
        timeZone="Asia/Kolkata"
        numberOfMonths={2}
      />
      <Box padding={16}>
        <div>{selected.from ? formatter.format(selected.from) : 'No start date'}</div>
        <div>
          {selected.to
            ? formatter.format(endOfDay(new TZDate(selected.to, 'Asia/Kolkata')))
            : 'No end date'}
        </div>
      </Box>
    </Box>
  );
};
