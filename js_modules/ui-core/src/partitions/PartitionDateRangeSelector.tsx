import {Button, Icon, Menu, MenuItem, Popover} from '@dagster-io/ui-components';
import dayjs from 'dayjs';
import * as React from 'react';

import {
  PartitionDateFilter,
  RECENT_PARTITIONS_LABEL,
  recentPartitionsFilter,
} from './partitionDateFilter';
import {TimeContext} from '../app/time/TimeContext';
import {testId} from '../testing/testId';
import {DateRangeDialog} from '../ui/DateRangeDialog';
import '../util/dayjsExtensions';

const ALL_TIME_LABEL = 'All time';

interface DateRangeOption {
  key: string;
  label: string;
  getRange: (tz: string) => {from: dayjs.Dayjs; to: dayjs.Dayjs} | null;
}

const HIGH_RESOLUTION_OPTIONS: DateRangeOption[] = [
  {
    key: 'today',
    label: 'Today',
    getRange: (tz) => ({from: dayjs().tz(tz).startOf('day'), to: dayjs().tz(tz).endOf('day')}),
  },
  {
    key: 'last_2_days',
    label: 'Last 2 days',
    getRange: (tz) => ({
      from: dayjs().tz(tz).subtract(1, 'day').startOf('day'),
      to: dayjs().tz(tz).endOf('day'),
    }),
  },
];

const DATE_RANGE_OPTIONS: DateRangeOption[] = [
  {
    key: 'last_7',
    label: 'Last 7 days',
    getRange: (tz) => ({
      from: dayjs().tz(tz).subtract(7, 'day').startOf('day'),
      to: dayjs().tz(tz).endOf('day'),
    }),
  },
  {
    key: 'last_30',
    label: 'Last 30 days',
    getRange: (tz) => ({
      from: dayjs().tz(tz).subtract(30, 'day').startOf('day'),
      to: dayjs().tz(tz).endOf('day'),
    }),
  },
  {
    key: 'last_90',
    label: RECENT_PARTITIONS_LABEL,
    getRange: (tz) => recentPartitionsFilter(tz),
  },
  {
    key: 'this_month',
    label: 'This month',
    getRange: (tz) => ({from: dayjs().tz(tz).startOf('month'), to: dayjs().tz(tz).endOf('day')}),
  },
  {
    key: 'last_month',
    label: 'Last month',
    getRange: (tz) => ({
      from: dayjs().tz(tz).subtract(1, 'month').startOf('month'),
      to: dayjs().tz(tz).subtract(1, 'month').endOf('month'),
    }),
  },
  {key: 'all_time', label: ALL_TIME_LABEL, getRange: () => null},
  {key: 'custom', label: 'Custom\u2026', getRange: () => null},
];

/**
 * Renders a date-range dropdown button with preset options and a custom date
 * range dialog. The active range is owned by the parent; the button label comes
 * from the filter itself so a filter applied elsewhere (e.g. a default window)
 * is described correctly here.
 */
export const PartitionDateRangeSelector = ({
  filter,
  onFilterChange,
  isHighResolution,
}: {
  filter: PartitionDateFilter | null;
  onFilterChange: (filter: PartitionDateFilter | null) => void;
  isHighResolution: boolean;
}) => {
  const {resolvedTimezone} = React.useContext(TimeContext);
  const [showCustomDialog, setShowCustomDialog] = React.useState(false);

  const label = filter?.label ?? ALL_TIME_LABEL;

  const options = React.useMemo(
    () =>
      isHighResolution ? [...HIGH_RESOLUTION_OPTIONS, ...DATE_RANGE_OPTIONS] : DATE_RANGE_OPTIONS,
    [isHighResolution],
  );

  const handleSelect = (option: DateRangeOption) => {
    if (option.key === 'custom') {
      setShowCustomDialog(true);
      return;
    }
    const range = option.getRange(resolvedTimezone);
    onFilterChange(range ? {...range, label: option.label} : null);
  };

  const handleCustomApply = (value: [number | null, number | null]) => {
    setShowCustomDialog(false);

    const [fromMs, toMs] = value;
    if (fromMs != null && toMs != null) {
      const from = dayjs(fromMs).tz(resolvedTimezone);
      const to = dayjs(toMs).tz(resolvedTimezone);

      const fromLabel = from.toDate().toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'numeric',
        day: 'numeric',
        timeZone: resolvedTimezone,
      });
      const toLabel = to.toDate().toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'numeric',
        day: 'numeric',
        timeZone: resolvedTimezone,
      });

      onFilterChange({from, to, label: `${fromLabel} \u2013 ${toLabel}`});
    }
  };

  return (
    <>
      <Popover
        placement="bottom-end"
        content={
          <Menu>
            {options.map((option) => (
              <MenuItem
                key={option.key}
                text={option.label}
                icon="date"
                active={option.label === label}
                onClick={() => handleSelect(option)}
              />
            ))}
          </Menu>
        }
      >
        <Button
          rightIcon={<Icon name="arrow_drop_down" />}
          data-testid={testId('date-range-partition-button')}
        >
          {label}
        </Button>
      </Popover>
      <DateRangeDialog
        isOpen={showCustomDialog}
        onCancel={() => setShowCustomDialog(false)}
        onApply={handleCustomApply}
      />
    </>
  );
};
