import {Box, Colors} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {assertUnreachable} from '../../app/Util';
import {StaleStatus} from '../../graphql/types';
import {StaticBaseConfig, useStaticSetFilter} from '../BaseFilters/useStaticSetFilter';

const emptyArray: any[] = [];

export const useStaleStatusFilter = ({
  allStaleStatuses = Object.values(StaleStatus),
  staleStatuses,
  setStaleStatuses,
}: {
  allStaleStatuses?: StaleStatus[];
  staleStatuses?: null | StaleStatus[];
  setStaleStatuses?: null | ((s: StaleStatus[]) => void);
}) => {
  return useStaticSetFilter<StaleStatus>({
    ...BaseConfig,
    allValues: useMemo(
      () =>
        allStaleStatuses.map((value) => ({
          value,
          match: [getStatusString(value)],
        })),
      [allStaleStatuses],
    ),
    menuWidth: '300px',
    state: staleStatuses ?? emptyArray,
    onStateChanged: (values) => {
      setStaleStatuses?.(Array.from(values));
    },
    canSelectAll: true,
  });
};

function getStatusString(status: StaleStatus): string {
  switch (status) {
    case StaleStatus.FRESH:
      return 'Fresh';
    case StaleStatus.STALE:
      return 'Stale';
    case StaleStatus.MISSING:
      return 'Missing';
    default:
      return assertUnreachable(status);
  }
}

function getStatusColor(status: StaleStatus): string {
  switch (status) {
    case StaleStatus.FRESH:
      return Colors.accentGreen();
    case StaleStatus.STALE:
      return Colors.accentYellow();
    case StaleStatus.MISSING:
      return Colors.accentGray();
    default:
      return assertUnreachable(status);
  }
}

export const BaseConfig: StaticBaseConfig<StaleStatus> = {
  name: 'Status',
  icon: 'status',
  renderLabel: ({value}) => (
    <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
      <span style={{color: getStatusColor(value)}}>●</span>
      {getStatusString(value)}
    </Box>
  ),
  getStringValue: (status) => getStatusString(status),
  getKey: getStatusString,
  matchType: 'any-of',
};
