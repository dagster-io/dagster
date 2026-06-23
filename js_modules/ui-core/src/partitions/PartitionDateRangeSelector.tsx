import {Button, Icon, Menu, MenuItem, Popover} from '@dagster-io/ui-components';
import dayjs from 'dayjs';
import * as React from 'react';

import {TimeContext} from '../app/time/TimeContext';
import {testId} from '../testing/testId';
import {DateRangeDialog} from '../ui/DateRangeDialog';
import '../util/dayjsExtensions';

interface DateRangeOption {
  key: string;
  label: string;
  getRange: (tz: string) => [dayjs.Dayjs, dayjs.Dayjs] | null;
}

const HIGH_RESOLUTION_OPTIONS: DateRangeOption[] = [
  {
    key: 'today',
    label: 'Today',
    getRange: (tz) => [dayjs().tz(tz).startOf('day'), dayjs().tz(tz).endOf('day')],
  },
  {
    key: 'last_2_days',
    label: 'Last 2 days',
    getRange: (tz) => [
      dayjs().tz(tz).subtract(1, 'day').startOf('day'),
      dayjs().tz(tz).endOf('day'),
    ],
  },
];

const DATE_RANGE_OPTIONS: DateRangeOption[] = [
  {
    key: 'last_7',
    label: 'Last 7 days',
    getRange: (tz) => [
      dayjs().tz(tz).subtract(7, 'day').startOf('day'),
      dayjs().tz(tz).endOf('day'),
    ],
  },
  {
    key: 'last_30',
    label: 'Last 30 days',
    getRange: (tz) => [
      dayjs().tz(tz).subtract(30, 'day').startOf('day'),
      dayjs().tz(tz).endOf('day'),
    ],
  },
  {
    key: 'last_90',
    label: 'Last 90 days',
    getRange: (tz) => [
      dayjs().tz(tz).subtract(90, 'day').startOf('day'),
      dayjs().tz(tz).endOf('day'),
    ],
  },
  {
    key: 'this_month',
    label: 'This month',
    getRange: (tz) => [dayjs().tz(tz).startOf('month'), dayjs().tz(tz).endOf('day')],
  },
  {
    key: 'last_month',
    label: 'Last month',
    getRange: (tz) => [
      dayjs().tz(tz).subtract(1, 'month').startOf('month'),
      dayjs().tz(tz).subtract(1, 'month').endOf('month'),
    ],
  },
  {key: 'all_time', label: 'All time', getRange: () => null},
  {key: 'custom', label: 'Custom\u2026', getRange: () => null},
];

/**
 * Renders a date-range dropdown button with preset options and a custom date
 * range dialog. Manages its own transient UI state (menu open, dialog open,
 * display label) and notifies the parent of filter changes via callback.
 */
export const PartitionDateRangeSelector = ({
  filter,
  onFilterChange,
  isHighResolution,
}: {
  filter: [dayjs.Dayjs, dayjs.Dayjs] | null;
  onFilterChange: (filter: [dayjs.Dayjs, dayjs.Dayjs] | null) => void;
  isHighResolution: boolean;
}) => {
  const {resolvedTimezone} = React.useContext(TimeContext);
  const [showCustomDialog, setShowCustomDialog] = React.useState(false);
  const [label, setLabel] = React.useState('All time');

  React.useEffect(() => {
    if (!filter) {
      setLabel('All time');
    }
  }, [filter]);

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
    setLabel(option.label);
    onFilterChange(option.getRange(resolvedTimezone));
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

      setLabel(`${fromLabel} \u2013 ${toLabel}`);
      onFilterChange([from, to]);
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
