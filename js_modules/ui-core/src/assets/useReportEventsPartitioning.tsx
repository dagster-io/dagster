import {useState} from 'react';

import {useQuery} from '../apollo-client';
import {mergedAssetHealth} from './MultipartitioningSupport';
import {REPORT_EVENT_PARTITION_DEFINITION_QUERY} from './ReportEventsQueries';
import {asAssetKeyInput} from './asInput';
import {usePartitionDimensionSelections} from './usePartitionDimensionSelections';
import {usePartitionHealthData} from './usePartitionHealthData';
import {AssetKeyInput, PartitionDefinitionType} from '../graphql/types';
import {
  ReportEventPartitionDefinitionQuery,
  ReportEventPartitionDefinitionQueryVariables,
} from './types/ReportEventsQueries.types';

export function useReportEventsPartitioning(assetKey: AssetKeyInput, isPartitioned: boolean) {
  const assetPartitionDefResult = useQuery<
    ReportEventPartitionDefinitionQuery,
    ReportEventPartitionDefinitionQueryVariables
  >(REPORT_EVENT_PARTITION_DEFINITION_QUERY, {
    variables: {
      assetKey: asAssetKeyInput(assetKey),
    },
  });

  const assetPartitionDef =
    assetPartitionDefResult.data?.assetNodeOrError.__typename === 'AssetNode'
      ? assetPartitionDefResult.data?.assetNodeOrError.partitionDefinition
      : null;

  // LastRefresh is a hint value that can be used to request a rebuild of the partition
  // health data. It's used when dynamic partitions are added.
  const [lastRefresh, setLastRefresh] = useState(Date.now());

  const assetHealth = mergedAssetHealth(
    usePartitionHealthData(isPartitioned ? [assetKey] : [], lastRefresh.toString(), 'background'),
  );

  const isDynamic = assetHealth.dimensions.some((d) => d.type === PartitionDefinitionType.DYNAMIC);
  const [selections, setSelections] = usePartitionDimensionSelections({
    assetHealth,
    modifyQueryString: false,
    skipPartitionKeyValidation: isDynamic,
    shouldReadPartitionQueryStringParam: true,
    defaultSelection: 'empty',
  });

  return {assetPartitionDef, assetHealth, selections, setSelections, setLastRefresh};
}
