import {gql, useQuery} from '@apollo/client';
import {Box, ButtonGroup, Colors, NonIdealState, Spinner, Subheading} from '@dagster-io/ui';
import * as React from 'react';

import {LiveDataForNode} from '../asset-graph/Utils';
import {METADATA_ENTRY_FRAGMENT} from '../metadata/MetadataEntry';
import {SidebarSection} from '../pipelines/SidebarComponents';
import {RepositorySelector} from '../types/globalTypes';

import {AssetEventsTable} from './AssetEventsTable';
import {ASSET_LINEAGE_FRAGMENT} from './AssetLineageElements';
import {AssetMaterializationGraphs} from './AssetMaterializationGraphs';
import {AssetViewParams} from './AssetView';
import {CurrentRunsBanner} from './CurrentRunsBanner';
import {FailedRunsSinceMaterializationBanner} from './FailedRunsSinceMaterializationBanner';
import {LatestMaterializationMetadata} from './LastMaterializationMetadata';
import {AssetEventGroup, groupByPartition} from './groupByPartition';
import {AssetKey} from './types';
import {AssetEventsQuery, AssetEventsQueryVariables} from './types/AssetEventsQuery';

interface Props {
  assetKey: AssetKey;
  asSidebarSection?: boolean;
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

/**
 * If the asset has a defined partition space, we load all materializations in the
 * last 100 partitions. This ensures that if you run a huge backfill of old partitions,
 * you still see accurate info for the last 100 partitions in the UI. A count-based
 * limit could cause random partitions to disappear if materializations were out of order.
 */
function useRecentAssetEvents(
  assetKey: AssetKey,
  assetHasDefinedPartitions: boolean,
  xAxis: 'partition' | 'time',
  before?: string,
) {
  const loadUsingPartitionKeys = assetHasDefinedPartitions && xAxis === 'partition';

  const {data, loading, refetch} = useQuery<AssetEventsQuery, AssetEventsQueryVariables>(
    ASSET_EVENTS_QUERY,
    {
      variables: loadUsingPartitionKeys
        ? {
            assetKey: {path: assetKey.path},
            before,
            partitionInLast: 120,
          }
        : {
            assetKey: {path: assetKey.path},
            before,
            limit: 100,
          },
    },
  );

  return React.useMemo(() => {
    const asset =
      data?.materializedKeyOrError.__typename === 'MaterializedKey'
        ? data?.materializedKeyOrError
        : null;
    const materializations = asset?.assetMaterializations || [];
    const observations = asset?.assetObservations || [];

    const allPartitionKeys = asset?.assetNode?.partitionKeys;
    const loadedPartitionKeys =
      loadUsingPartitionKeys && allPartitionKeys
        ? allPartitionKeys.slice(allPartitionKeys.length - 120)
        : undefined;

    return {asset, loadedPartitionKeys, materializations, observations, loading, refetch};
  }, [data, loading, refetch, loadUsingPartitionKeys]);
}

export const AssetEvents: React.FC<Props> = ({
  assetKey,
  assetLastMaterializedAt,
  assetHasDefinedPartitions,
  asSidebarSection,
  params,
  setParams,
  liveData,
}) => {
  const before = params.asOf ? `${Number(params.asOf) + 1}` : undefined;
  const xAxisDefault = assetHasDefinedPartitions ? 'partition' : 'time';
  const xAxis =
    assetHasDefinedPartitions && params.partition !== undefined
      ? 'partition'
      : params.time !== undefined || before
      ? 'time'
      : xAxisDefault;

  const {
    materializations,
    observations,
    loadedPartitionKeys,
    loading,
    refetch,
  } = useRecentAssetEvents(assetKey, assetHasDefinedPartitions, xAxis, before);

  React.useEffect(() => {
    if (params.asOf) {
      return;
    }
    refetch();
  }, [params.asOf, assetLastMaterializedAt, refetch]);

  const grouped = React.useMemo<AssetEventGroup[]>(() => {
    const events = [...materializations, ...observations].sort(
      (b, a) => Number(a.timestamp) - Number(b.timestamp),
    );
    if (xAxis === 'partition' && loadedPartitionKeys) {
      return groupByPartition(events, loadedPartitionKeys);
    } else {
      // return a group for every materialization to achieve un-grouped rendering
      return events.map((event) => ({
        latest: event,
        partition: event.partition || undefined,
        timestamp: event.timestamp,
        all: [],
      }));
    }
  }, [loadedPartitionKeys, materializations, observations, xAxis]);

  const activeItems = React.useMemo(() => new Set([xAxis]), [xAxis]);

  const onSetFocused = (group: AssetEventGroup) => {
    const updates: Partial<AssetViewParams> =
      xAxis === 'time'
        ? {time: group.timestamp !== params.time ? group.timestamp : ''}
        : {partition: group.partition !== params.partition ? group.partition : ''};
    setParams({...params, ...updates});
  };

  if (process.env.NODE_ENV === 'test') {
    return <span />; // chartjs and our useViewport hook don't play nicely with jest
  }

  if (asSidebarSection) {
    const latest = materializations[0];

    if (loading) {
      return (
        <Box padding={{vertical: 20}}>
          <Spinner purpose="section" />
        </Box>
      );
    }
    return (
      <>
        <FailedRunsSinceMaterializationBanner liveData={liveData} />
        <CurrentRunsBanner liveData={liveData} />
        <SidebarSection title="Materialization in Last Run">
          {latest ? (
            <div style={{margin: -1, maxWidth: '100%', overflowX: 'auto'}}>
              <LatestMaterializationMetadata latest={latest} />
            </div>
          ) : (
            <Box
              margin={{horizontal: 24, vertical: 12}}
              style={{color: Colors.Gray500, fontSize: '0.8rem'}}
            >
              No materializations found
            </Box>
          )}
        </SidebarSection>
        <SidebarSection title="Metadata Plots">
          <AssetMaterializationGraphs xAxis={xAxis} asSidebarSection groups={grouped} />
        </SidebarSection>
      </>
    );
  }

  const focused =
    grouped.find((b) =>
      params.time
        ? Number(b.timestamp) <= Number(params.time)
        : params.partition
        ? b.partition === params.partition
        : false,
    ) ||
    grouped[0] ||
    null;

  if (loading) {
    return (
      <Box style={{display: 'flex'}}>
        <Box style={{flex: 1}}>
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
        <Box style={{width: '40%'}} border={{side: 'left', color: Colors.KeylineGray, width: 1}} />
      </Box>
    );
  }

  return (
    <Box style={{display: 'flex', flex: 1}}>
      <Box style={{flex: 1}}>
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
                      ? {...params, partition: undefined, time: focused.timestamp || ''}
                      : {...params, partition: focused.partition || '', time: undefined},
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
        {/** Ensures the line between the left and right columns goes to the bottom of the page */}
        <div style={{flex: 1}} />
      </Box>
      <Box style={{width: '40%'}} border={{side: 'left', color: Colors.KeylineGray, width: 1}}>
        <AssetMaterializationGraphs
          xAxis={xAxis}
          asSidebarSection={asSidebarSection}
          groups={grouped}
        />
      </Box>
    </Box>
  );
};

const ASSET_EVENTS_QUERY = gql`
  query AssetEventsQuery(
    $assetKey: AssetKeyInput!
    $limit: Int
    $before: String
    $partitionInLast: Int
  ) {
    materializedKeyOrError(assetKey: $assetKey) {
      ... on MaterializedKey {
        id
        key {
          path
        }
        assetObservations(
          limit: $limit
          beforeTimestampMillis: $before
          partitionInLast: $partitionInLast
        ) {
          ...AssetObservationFragment
        }
        assetMaterializations(
          limit: $limit
          beforeTimestampMillis: $before
          partitionInLast: $partitionInLast
        ) {
          ...AssetMaterializationFragment
        }

        assetNode {
          id
          partitionKeys
        }
      }
    }
  }
  fragment AssetMaterializationFragment on MaterializationEvent {
    partition
    runOrError {
      ... on PipelineRun {
        id
        runId
        mode
        repositoryOrigin {
          id
          repositoryName
          repositoryLocationName
        }
        status
        pipelineName
        pipelineSnapshotId
      }
    }
    runId
    timestamp
    stepKey
    label
    description
    metadataEntries {
      ...MetadataEntryFragment
    }
    assetLineage {
      ...AssetLineageFragment
    }
  }
  fragment AssetObservationFragment on ObservationEvent {
    partition
    runOrError {
      ... on PipelineRun {
        id
        runId
        mode
        repositoryOrigin {
          id
          repositoryName
          repositoryLocationName
        }
        status
        pipelineName
        pipelineSnapshotId
      }
    }
    runId
    timestamp
    stepKey
    label
    description
    metadataEntries {
      ...MetadataEntryFragment
    }
  }
  ${METADATA_ENTRY_FRAGMENT}
  ${ASSET_LINEAGE_FRAGMENT}
`;
