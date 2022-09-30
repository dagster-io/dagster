import {Box, ButtonGroup, Colors, NonIdealState, Spinner, Subheading} from '@dagster-io/ui';
import * as React from 'react';

import {LiveDataForNode} from '../asset-graph/Utils';
import {RepositorySelector} from '../types/globalTypes';

import {AssetEventsTable} from './AssetEventsTable';
import {AssetViewParams} from './AssetView';
import {CurrentRunsBanner} from './CurrentRunsBanner';
import {FailedRunsSinceMaterializationBanner} from './FailedRunsSinceMaterializationBanner';
import {AssetEventGroup, useGroupedEvents} from './groupByPartition';
import {AssetKey} from './types';
import {useRecentAssetEvents} from './useRecentAssetEvents';

interface Props {
  assetKey: AssetKey;
  liveData?: LiveDataForNode;
  params: AssetViewParams;
  paramsTimeWindowOnly: boolean;
  setParams: (params: AssetViewParams) => void;

  // This timestamp is a "hint", when it changes this component will refetch
  // to retrieve new data. Just don't want to poll the entire table query.
  assetLastMaterializedAt: string | undefined;

  // This is passed in because we need to know whether to default to partition
  // grouping /before/ loading all the data.
  assetHasDefinedPartitions: boolean;
  repository?: RepositorySelector;
  opName?: string | null;
}

export const AssetEvents: React.FC<Props> = ({
  assetKey,
  assetLastMaterializedAt,
  assetHasDefinedPartitions,
  params,
  setParams,
  liveData,
}) => {
  const {
    xAxis,
    materializations,
    observations,
    loadedPartitionKeys,
    loading,
    refetch,
  } = useRecentAssetEvents(assetKey, assetHasDefinedPartitions, params);

  React.useEffect(() => {
    if (params.asOf) {
      return;
    }
    refetch();
  }, [params.asOf, assetLastMaterializedAt, refetch]);

  const grouped = useGroupedEvents(xAxis, materializations, observations, loadedPartitionKeys);
  const activeItems = React.useMemo(() => new Set([xAxis]), [xAxis]);

  const onSetFocused = (group: AssetEventGroup | undefined) => {
    const updates: Partial<AssetViewParams> =
      xAxis === 'time'
        ? {time: group?.timestamp !== params.time ? group?.timestamp || '' : ''}
        : {partition: group?.partition !== params.partition ? group?.partition || '' : ''};
    setParams({...params, ...updates});
  };

  let focused: AssetEventGroup | undefined = grouped.find((b) =>
    params.time
      ? Number(b.timestamp) <= Number(params.time)
      : params.partition
      ? b.partition === params.partition
      : false,
  );

  if (params.time === undefined && params.partition === undefined) {
    // default to expanding the first row in the table so users know how much
    // detail exists within each item.
    focused = grouped[0];
  }

  if (loading) {
    return (
      <Box>
        <Box
          flex={{justifyContent: 'space-between', alignItems: 'center'}}
          padding={{vertical: 16, horizontal: 24}}
          style={{marginBottom: -1}}
        >
          <Subheading>Asset Events</Subheading>
        </Box>
        <Box padding={{vertical: 20}}>
          <Spinner purpose="section" />
        </Box>
      </Box>
    );
  }

  return (
    <Box>
      <Box
        flex={{justifyContent: 'space-between', alignItems: 'center'}}
        padding={{vertical: 16, horizontal: 24}}
        style={{marginBottom: -1}}
      >
        <Subheading>Asset Events</Subheading>
        {assetHasDefinedPartitions ? (
          <div style={{margin: '-6px 0 '}}>
            <ButtonGroup
              activeItems={activeItems}
              buttons={[
                {id: 'partition', label: 'By partition'},
                {id: 'time', label: 'By timestamp'},
              ]}
              onClick={(id: string) =>
                setParams(
                  id === 'time'
                    ? {...params, partition: undefined, time: focused?.timestamp || ''}
                    : {...params, partition: focused?.partition || '', time: undefined},
                )
              }
            />
          </div>
        ) : null}
      </Box>
      <FailedRunsSinceMaterializationBanner liveData={liveData} />
      <CurrentRunsBanner liveData={liveData} />
      {grouped.length > 0 ? (
        <AssetEventsTable
          hasPartitions={assetHasDefinedPartitions}
          hasLineage={materializations.some((m) => m.assetLineage.length > 0)}
          groups={grouped}
          focused={focused}
          setFocused={onSetFocused}
        />
      ) : (
        <Box padding={{vertical: 20}} border={{side: 'top', color: Colors.KeylineGray, width: 1}}>
          <NonIdealState
            icon="materialization"
            title="No materializations"
            description="No materializations were found for this asset."
          />
        </Box>
      )}
      {loadedPartitionKeys && (
        <Box padding={{vertical: 16, horizontal: 24}} style={{color: Colors.Gray400}}>
          Showing materializations for the last {loadedPartitionKeys.length} partitions.
        </Box>
      )}
    </Box>
  );
};
