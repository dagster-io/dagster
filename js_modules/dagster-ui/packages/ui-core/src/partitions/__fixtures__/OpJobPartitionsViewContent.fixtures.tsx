import {
  buildPartition,
  buildPartitionSet,
  buildPartitions,
  buildPythonError,
} from '../../graphql/types';
import {OpJobPartitionSetFragment} from '../types/OpJobPartitionsView.types';

export const buildOpJobPartitionSetFragmentWithError = (): OpJobPartitionSetFragment => {
  return buildPartitionSet({
    id: 'my-partition-set',
    name: 'my-partition-set',
    pipelineName: 'my-job',
    partitionRuns: [],
    partitionsOrError: buildPartitions({
      results: [buildPartition({name: 'lorem'}), buildPartition({name: 'ipsum'})],
    }),
    partitionStatusesOrError: buildPythonError({
      message: 'total fail',
    }),
  });
};
