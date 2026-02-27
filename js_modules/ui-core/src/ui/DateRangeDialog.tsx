import {
  Button,
  Colors,
  DateRange,
  Dialog,
  DialogBody,
  DialogFooter,
  Matcher,
} from '@dagster-io/ui-components';
import {TZDate} from '@date-fns/tz';
import {endOfDay} from 'date-fns';
import dayjs from 'dayjs';
import memoize from 'lodash/memoize';
import {useContext, useEffect, useMemo, useState} from 'react';

import {TimeContext} from '../app/time/TimeContext';
import {lazy} from '../util/lazy';

const DayPickerWrapper = lazy(() => import('./DayPickerWrapperForLazyImport'));

export type DialogProps = {
  isOpen: boolean;
  onCancel: () => void;
  onApply: (value: [number | null, number | null]) => void;
  hidden?: Matcher[];
};

const buildFormatter = memoize(
  (timeZone: string) =>
    new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      timeZone,
    }),
);

export function DateRangeDialog({onCancel, onApply, isOpen, hidden}: DialogProps) {
  const {resolvedTimezone: targetTimezone} = useContext(TimeContext);

  const [selected, setSelected] = useState<DateRange>(() => ({from: undefined, to: undefined}));

  // Reset the dialog when it's closed so you are always prompted to choose a new date range.
  useEffect(() => {
    if (!isOpen) {
      setSelected({from: undefined, to: undefined});
    }
  }, [isOpen]);

  const formatter = buildFormatter(targetTimezone);
  const startMonth = useMemo(() => dayjs().subtract(1, 'month').toDate(), []);

  const leftContent = () => {
    if (selected.from) {
      if (selected.to) {
        return (
          <div>
            <span style={{color: Colors.textLight()}}>Selected:</span>{' '}
            {formatter.format(selected.from)} - {formatter.format(selected.to)}
          </div>
        );
      }
      return (
        <div>
          Selected{' '}
          <span style={{color: Colors.textLight()}}>{formatter.format(selected.from)}</span>
        </div>
      );
    }

    return null;
  };

  return (
    <Dialog
      isOpen={isOpen}
      title="Select a date range"
      onClosed={onCancel}
      style={{width: 'auto', minWidth: 688}}
    >
      <DialogBody>
        <div style={{height: '344px'}}>
          <DayPickerWrapper
            timeZone={targetTimezone}
            mode="range"
            navLayout="around"
            selected={selected}
            onSelect={setSelected}
            excludeDisabled
            required
            defaultMonth={startMonth}
            numberOfMonths={2}
            hidden={hidden}
          />
        </div>
      </DialogBody>
      <DialogFooter topBorder left={leftContent()}>
        <Button onClick={() => onCancel()}>Cancel</Button>
        <Button
          intent="primary"
          disabled={!selected.from || !selected.to}
          onClick={() => {
            if (selected.from && selected.to) {
              const endDateEndOfDay = endOfDay(new TZDate(selected.to, targetTimezone));
              onApply([selected.from.valueOf(), endDateEndOfDay.valueOf()]);
            }
          }}
        >
          Apply
        </Button>
      </DialogFooter>
    </Dialog>
  );
}
