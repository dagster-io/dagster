import {BulkActionStatus} from '../graphql/types';
import {useStaticSetFilter} from '../ui/BaseFilters/useStaticSetFilter';

const labelForBackfillStatus = (key: BulkActionStatus) => {
  switch (key) {
    case BulkActionStatus.CANCELED:
      return 'Canceled';
    case BulkActionStatus.CANCELING:
      return 'Canceling';
    case BulkActionStatus.COMPLETED:
      return 'Completed';
    case BulkActionStatus.FAILED:
      return 'Failed';
    case BulkActionStatus.REQUESTED:
      return 'In progress';
    case BulkActionStatus.COMPLETED_SUCCESS:
      return 'Success';
    case BulkActionStatus.COMPLETED_FAILED:
      return 'Failed';
  }
};

export function useBulkActionStatusFilter(
  state: Set<BulkActionStatus> | BulkActionStatus[],
  onStateChanged: (state: Set<BulkActionStatus>) => void,
) {
  const backfillStatusValues = Object.keys(BulkActionStatus).map((key) => {
    const status = key as BulkActionStatus;
    const label = labelForBackfillStatus(status);
    return {
      label,
      value: status,
      match: [status, label],
    };
  });

  const statusFilter = useStaticSetFilter<BulkActionStatus>({
    name: 'Status',
    icon: 'status',
    allValues: backfillStatusValues,
    allowMultipleSelections: false,
    closeOnSelect: true,
    renderLabel: ({value}) => <div>{labelForBackfillStatus(value)}</div>,
    getStringValue: (status) => labelForBackfillStatus(status),
    state,
    onStateChanged,
  });

  return statusFilter;
}
