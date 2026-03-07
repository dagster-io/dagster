import {Box} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {DagsterTag} from '../runs/RunTag';
import {RunsFeedTableWithFilters} from '../runs/RunsFeedTable';

interface PartitionRunListProps {
  pipelineName: string;
  partitionName: string;
}

export const PartitionRunList = (props: PartitionRunListProps) => {
  const filter = useMemo(
    () => ({
      pipelineName: props.pipelineName,
      tags: [{key: DagsterTag.Partition, value: props.partitionName}],
    }),
    [props.pipelineName, props.partitionName],
  );

  return (
    <Box flex={{direction: 'column'}} style={{minHeight: 0, maxHeight: '60vh'}}>
      <RunsFeedTableWithFilters filter={filter} includeRunsFromBackfills scroll />
    </Box>
  );
};
