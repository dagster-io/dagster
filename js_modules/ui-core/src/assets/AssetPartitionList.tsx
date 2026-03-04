import {AssetPartitionStatus, assetPartitionStatusesToStyle} from './AssetPartitionStatus';
import {PartitionListSelector, PartitionStatusDot} from './PartitionListSelector';

export interface AssetPartitionListProps {
  partitions: string[];
  statusForPartition: (dimensionKey: string) => AssetPartitionStatus[];
  focusedDimensionKey?: string;
  setFocusedDimensionKey?: (dimensionKey: string | undefined) => void;
}

const STATUS_ORDER: AssetPartitionStatus[] = [
  AssetPartitionStatus.MISSING,
  AssetPartitionStatus.FAILED,
  AssetPartitionStatus.MATERIALIZING,
  AssetPartitionStatus.MATERIALIZED,
];

export const AssetPartitionList = ({
  focusedDimensionKey,
  setFocusedDimensionKey,
  statusForPartition,
  partitions,
}: AssetPartitionListProps) => {
  return (
    <PartitionListSelector
      partitions={partitions}
      statusForPartition={statusForPartition}
      focusedDimensionKey={focusedDimensionKey}
      setFocusedDimensionKey={setFocusedDimensionKey}
      statusesToStyle={assetPartitionStatusesToStyle}
      statusOrder={STATUS_ORDER}
    />
  );
};

export const AssetPartitionStatusDot = ({status}: {status: AssetPartitionStatus[]}) => (
  <PartitionStatusDot status={status} statusesToStyle={assetPartitionStatusesToStyle} />
);
