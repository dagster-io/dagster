import {BulkActionStatus} from '../graphql/types';
import {useStaticSetFilter} from '../ui/BaseFilters/useStaticSetFilter';

const labelsForBackfillStatus: Record<BulkActionStatus, string> = {
  [BulkActionStatus.CANCELED]: 'Canceled',
  [BulkActionStatus.CANCELING]: 'Canceling',
  [BulkActionStatus.COMPLETED]: 'Completed',
  [BulkActionStatus.FAILED]: 'Failed',
  [BulkActionStatus.REQUESTED]: 'In progress',
  [BulkActionStatus.COMPLETED_SUCCESS]: 'Success',
  [BulkActionStatus.COMPLETED_FAILED]: 'Failed',
};

const backfillStatusValues = Object.keys(BulkActionStatus).map((key) => {
  const status = key as BulkActionStatus;
  const label = labelsForBackfillStatus[status];
  return {
    label,
    value: status,
    match: [status, label],
  };
});

export function useBulkActionStatusFilter(
  state: Set<BulkActionStatus> | BulkActionStatus[],
  onStateChanged: (state: Set<BulkActionStatus>) => void,
) {
  const statusFilter = useStaticSetFilter<BulkActionStatus>({
    name: 'Status',
    icon: 'status',
    allValues: backfillStatusValues,
    allowMultipleSelections: false,
    closeOnSelect: true,
    renderLabel: ({value}) => <div>{labelsForBackfillStatus[value]}</div>,
    getStringValue: (status) => labelsForBackfillStatus[status],
    state,
    onStateChanged,
  });

  return statusFilter;
}
