import {AssetPartitionStatus, assetPartitionStatusToText} from './AssetPartitionStatus';
import {PartitionStatusCheckboxes} from './PartitionStatusCheckboxes';

export const AssetPartitionStatusCheckboxes = ({
  counts,
  value,
  onChange,
  allowed,
  disabled,
}: {
  counts: {[status: string]: number};
  value: AssetPartitionStatus[];
  allowed: AssetPartitionStatus[];
  onChange: (selected: AssetPartitionStatus[]) => void;
  disabled?: boolean;
}) => {
  return (
    <PartitionStatusCheckboxes
      counts={counts}
      value={value}
      onChange={onChange}
      allowed={allowed}
      statusToText={assetPartitionStatusToText}
      disabled={disabled}
    />
  );
};
