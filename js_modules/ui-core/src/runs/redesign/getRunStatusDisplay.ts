import {Colors, IconName} from '@dagster-io/ui-components';

import {MappedRunsFeedEntry} from './mapRunsFeedData';
import {BulkActionStatus, RunStatus} from '../../graphql/types';
import {runStatusToBackfillStateString} from '../RunStatusTag';

export type TimingMode =
  | 'placeholder'
  | 'elapsed-since-creation'
  | 'elapsed-since-start'
  | 'relative-finish-time';

type StatusDisplay = {
  icon: IconName | 'spinner';
  iconColor: string;
  label: string;
  timingMode: TimingMode;
  timingColor: 'textBlue' | 'textYellow' | 'textLighter';
  isPulsing: boolean;
};

const RUN_STATUS_DISPLAYS = {
  [RunStatus.NOT_STARTED]: {
    icon: 'dagster_primary',
    iconColor: Colors.accentGray(),
    label: 'Not started',
    timingMode: 'placeholder',
    timingColor: 'textLighter',
    isPulsing: false,
  },
  [RunStatus.QUEUED]: {
    icon: 'dagster_primary',
    iconColor: Colors.accentBlue(),
    label: 'Queued',
    timingMode: 'elapsed-since-creation',
    timingColor: 'textBlue',
    isPulsing: false,
  },
  [RunStatus.STARTING]: {
    icon: 'status',
    iconColor: Colors.accentBlue(),
    label: 'Starting',
    timingMode: 'placeholder',
    timingColor: 'textBlue',
    isPulsing: true,
  },
  [RunStatus.STARTED]: {
    icon: 'spinner',
    iconColor: Colors.accentBlue(),
    label: 'Started',
    timingMode: 'elapsed-since-start',
    timingColor: 'textBlue',
    isPulsing: false,
  },
  [RunStatus.SUSPENDED]: {
    icon: 'status',
    iconColor: Colors.accentBlue(),
    label: 'Suspended',
    timingMode: 'elapsed-since-start',
    timingColor: 'textBlue',
    isPulsing: false,
  },
  [RunStatus.MANAGED]: {
    icon: 'spinner',
    iconColor: Colors.accentBlue(),
    label: 'Managed',
    timingMode: 'placeholder',
    timingColor: 'textBlue',
    isPulsing: false,
  },
  [RunStatus.CANCELING]: {
    icon: 'cancel',
    iconColor: Colors.accentYellow(),
    label: 'Canceling',
    timingMode: 'elapsed-since-start',
    timingColor: 'textYellow',
    isPulsing: true,
  },
  [RunStatus.SUCCESS]: {
    icon: 'check_filled',
    iconColor: Colors.accentGreen(),
    label: 'Success',
    timingMode: 'relative-finish-time',
    timingColor: 'textLighter',
    isPulsing: false,
  },
  [RunStatus.FAILURE]: {
    icon: 'error',
    iconColor: Colors.accentRed(),
    label: 'Failed',
    timingMode: 'relative-finish-time',
    timingColor: 'textLighter',
    isPulsing: false,
  },
  [RunStatus.CANCELED]: {
    icon: 'cancel',
    iconColor: Colors.accentYellow(),
    label: 'Canceled',
    timingMode: 'relative-finish-time',
    timingColor: 'textLighter',
    isPulsing: false,
  },
} as const satisfies Record<RunStatus, StatusDisplay>;

export const getRunStatusDisplay = (entry: MappedRunsFeedEntry): StatusDisplay => {
  const display = RUN_STATUS_DISPLAYS[entry.runStatus];
  if (entry.__typename === 'PartitionBackfill') {
    // FAILING maps to FAILURE while the backfill is still canceling its runs.
    if (entry.backfillStatus === BulkActionStatus.FAILING) {
      return {
        ...display,
        label: 'Failing',
        timingMode: 'elapsed-since-start',
        timingColor: 'textYellow',
        isPulsing: true,
      };
    }
    return {
      ...display,
      label: runStatusToBackfillStateString(entry.runStatus),
    };
  }

  if (entry.willRetry) {
    return {
      ...display,
      icon: 'replay',
      label: 'Failed (will retry)',
    };
  }

  return display;
};
