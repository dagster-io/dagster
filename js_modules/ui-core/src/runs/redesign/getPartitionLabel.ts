import {DagsterTag} from '../RunTag';

export const getPartitionLabel = (tags: Map<string, string>) => {
  const partition = tags.get(DagsterTag.Partition);
  if (partition !== undefined) {
    return partition;
  }

  const start = tags.get(DagsterTag.AssetPartitionRangeStart);
  const end = tags.get(DagsterTag.AssetPartitionRangeEnd);
  if (start !== undefined && end !== undefined) {
    return `${start} → ${end}`;
  }

  return null;
};
