import dayjs from 'dayjs';

import {ReportingMetricsGranularity} from './types';
import {assertUnreachable} from '../app/Util';
import {useFormatDateTime} from '../ui/useFormatDateTime';

export const DateRangeText = (props: {date: Date; granularity: ReportingMetricsGranularity}) => {
  const {date, granularity} = props;
  const formatDateTime = useFormatDateTime();

  switch (granularity) {
    case ReportingMetricsGranularity.MONTHLY: {
      const monthLabel = formatDateTime(date, {month: 'long', timeZone: 'UTC'});
      return <span>{monthLabel}</span>;
    }

    case ReportingMetricsGranularity.DAILY: {
      return <span>{formatDateTime(date, {month: 'short', day: 'numeric', timeZone: 'UTC'})}</span>;
    }

    case ReportingMetricsGranularity.WEEKLY: {
      const startDateLabel = formatDateTime(date, {
        month: 'short',
        day: 'numeric',
        timeZone: 'UTC',
      });
      const endDay = dayjs(date).add(1, 'week');
      const dayNow = dayjs(new Date());
      const endDateLabel = endDay.isAfter(dayNow)
        ? 'now'
        : formatDateTime(endDay.toDate(), {month: 'short', day: 'numeric', timeZone: 'UTC'});
      return <span>{`${startDateLabel} \u2013 ${endDateLabel}`}</span>;
    }

    default:
      return assertUnreachable(granularity);
  }
};
