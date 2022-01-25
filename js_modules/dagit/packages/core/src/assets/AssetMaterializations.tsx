import {gql, useQuery} from '@apollo/client';
import {
  Box,
  ButtonGroup,
  ColorsWIP,
  NonIdealState,
  Spinner,
  Caption,
  Subheading,
} from '@dagster-io/ui';
import flatMap from 'lodash/flatMap';
import uniq from 'lodash/uniq';
import * as React from 'react';

import {SidebarSection} from '../pipelines/SidebarComponents';
import {METADATA_ENTRY_FRAGMENT} from '../runs/MetadataEntry';
import {CurrentRunsBanner} from '../workspace/asset-graph/CurrentRunsBanner';
import {LiveDataForNode} from '../workspace/asset-graph/Utils';

import {ASSET_LINEAGE_FRAGMENT} from './AssetLineageElements';
import {AssetMaterializationTable} from './AssetMaterializationTable';
import {AssetValueGraph, AssetValueGraphData} from './AssetValueGraph';
import {AssetViewParams} from './AssetView';
import {LatestMaterializationMetadata} from './LastMaterializationMetadata';
import {MaterializationGroup, groupByPartition} from './groupByPartition';
import {AssetKey} from './types';
import {
  AssetMaterializationsQuery,
  AssetMaterializationsQueryVariables,
} from './types/AssetMaterializationsQuery';

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
  assetHasDefinedPartitions: boolean;
}

const LABEL_STEP_EXECUTION_TIME = 'Step Execution Time';

/**
 * If the asset has a defined partition space, we load all materializations in the
 * last 200 partitions. This ensures that if you run a huge backfill of old partitions,
 * you still see accurate info for the last 200 partitions in the UI. A count-based
 * limit could cause random partitions to disappear if materializations were out of order.
 *
 * For non-SDA-partitioned assets, we load the most recent 200 materializations. We might
 * still show these "By partition" (and the gaps problem above exists), but we don't have
 * a choice.
 */
function useRecentMaterializations(
  assetKey: AssetKey,
  assetHasDefinedPartitions: boolean,
  xAxis: 'partition' | 'time',
  before?: string,
) {
  const loadUsingPartitionKeys = assetHasDefinedPartitions && xAxis === 'partition';

  const {data, loading, refetch} = useQuery<
    AssetMaterializationsQuery,
    AssetMaterializationsQueryVariables
  >(ASSET_MATERIALIZATIONS_QUERY, {
    variables: loadUsingPartitionKeys
      ? {
          assetKey: {path: assetKey.path},
          before: before,
          partitionInLast: 120,
        }
      : {
          assetKey: {path: assetKey.path},
          before: before,
          limit: 200,
        },
  });

  return React.useMemo(() => {
    const asset = data?.assetOrError.__typename === 'Asset' ? data?.assetOrError : null;
    const materializations = asset?.assetMaterializations || [];
    const allPartitionKeys = asset?.definition?.partitionKeys;
    const requestedPartitionKeys =
      loadUsingPartitionKeys && allPartitionKeys
        ? allPartitionKeys.slice(allPartitionKeys.length - 120)
        : undefined;

    return {asset, requestedPartitionKeys, materializations, loading, refetch};
  }, [data, loading, refetch, loadUsingPartitionKeys]);
}

export const AssetMaterializations: React.FC<Props> = ({
  assetKey,
  assetLastMaterializedAt,
  assetHasDefinedPartitions,
  asSidebarSection,
  params,
  setParams,
  liveData,
}) => {
  const before = params.asOf ? `${Number(params.asOf) + 1}` : undefined;
  const xAxis =
    params.partition !== undefined
      ? 'partition'
      : params.time !== undefined || before
      ? 'time'
      : assetHasDefinedPartitions
      ? 'partition'
      : 'time';

  const {requestedPartitionKeys, materializations, loading, refetch} = useRecentMaterializations(
    assetKey,
    assetHasDefinedPartitions,
    xAxis,
    before,
  );

  React.useEffect(() => {
    if (params.asOf) {
      return;
    }
    refetch();
  }, [params.asOf, assetLastMaterializedAt, refetch]);

  const hasLineage = materializations.some((m) => m.assetLineage.length > 0);
  const hasPartitions = materializations.some((m) => m.partition) || assetHasDefinedPartitions;

  const grouped = React.useMemo<MaterializationGroup[]>(() => {
    if (!hasPartitions || xAxis !== 'partition') {
      return materializations.map((materialization) => ({
        latest: materialization,
        partition: materialization.partition || undefined,
        timestamp: materialization.timestamp,
        predecessors: [],
      }));
    }
    return groupByPartition(materializations, requestedPartitionKeys);
  }, [requestedPartitionKeys, hasPartitions, materializations, xAxis]);

  const activeItems = React.useMemo(() => new Set([xAxis]), [xAxis]);

  const onSetFocused = React.useCallback(
    (group) => {
      const updates: Partial<AssetViewParams> =
        xAxis === 'time'
          ? {time: group.timestamp !== params.time ? group.timestamp : undefined}
          : {partition: group.partition !== params.partition ? group.partition : undefined};
      setParams({...params, ...updates});
    },
    [setParams, params, xAxis],
  );

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
        <CurrentRunsBanner liveData={liveData} />
        <SidebarSection title="Materialization in Last Run">
          {latest ? (
            <div style={{margin: -1, maxWidth: '100%', overflowX: 'auto'}}>
              <LatestMaterializationMetadata latest={latest} />
            </div>
          ) : (
            <Box
              margin={{horizontal: 24, bottom: 24, top: 12}}
              style={{color: ColorsWIP.Gray500, fontSize: '0.8rem'}}
            >
              No materializations found
            </Box>
          )}
        </SidebarSection>
        <SidebarSection title="Materialization Plots">
          <AssetMaterializationGraphs
            xAxis={xAxis}
            asSidebarSection
            assetMaterializations={grouped}
          />
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
            <Subheading>Materializations</Subheading>
          </Box>
          <Box padding={{vertical: 20}}>
            <Spinner purpose="section" />
          </Box>
        </Box>
        <Box
          style={{width: '40%'}}
          border={{side: 'left', color: ColorsWIP.KeylineGray, width: 1}}
        ></Box>
      </Box>
    );
  }

  return (
    <Box style={{display: 'flex'}}>
      <Box style={{flex: 1}}>
        <Box
          flex={{justifyContent: 'space-between', alignItems: 'center'}}
          padding={{vertical: 16, horizontal: 24}}
          style={{marginBottom: -1}}
        >
          <Subheading>Materializations</Subheading>
          {hasPartitions ? (
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
        <CurrentRunsBanner liveData={liveData} />
        {grouped.length > 0 ? (
          <AssetMaterializationTable
            hasPartitions={hasPartitions}
            hasLineage={hasLineage}
            groups={grouped}
            focused={focused}
            setFocused={onSetFocused}
          />
        ) : (
          <Box
            padding={{vertical: 20}}
            border={{side: 'top', color: ColorsWIP.KeylineGray, width: 1}}
          >
            <NonIdealState
              icon="asset"
              title="No materializations"
              description="No materializations were found for this asset."
            />
          </Box>
        )}
        {requestedPartitionKeys && (
          <Box padding={{vertical: 16, horizontal: 24}} style={{color: ColorsWIP.Gray400}}>
            Showing materializations for the last {requestedPartitionKeys.length} partitions.
          </Box>
        )}
      </Box>
      <Box style={{width: '40%'}} border={{side: 'left', color: ColorsWIP.KeylineGray, width: 1}}>
        <AssetMaterializationGraphs
          xAxis={xAxis}
          asSidebarSection={asSidebarSection}
          assetMaterializations={grouped}
        />
      </Box>
    </Box>
  );
};

const AssetMaterializationGraphs: React.FC<{
  assetMaterializations: MaterializationGroup[];
  xAxis: 'partition' | 'time';
  asSidebarSection?: boolean;
}> = (props) => {
  const [xHover, setXHover] = React.useState<string | number | null>(null);

  const assetMaterializations = React.useMemo(() => {
    return [...props.assetMaterializations].reverse();
  }, [props.assetMaterializations]);

  const graphDataByMetadataLabel = extractNumericData(assetMaterializations, props.xAxis);
  const [graphedLabels] = React.useState(() => Object.keys(graphDataByMetadataLabel).slice(0, 4));

  return (
    <>
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'stretch',
          flexDirection: 'column',
        }}
      >
        {[...graphedLabels].sort().map((label) => (
          <Box
            key={label}
            style={{width: '100%'}}
            border={{side: 'bottom', width: 1, color: ColorsWIP.KeylineGray}}
          >
            {props.asSidebarSection ? (
              <Box padding={{horizontal: 24, top: 8}}>
                <Caption style={{fontWeight: 700}}>{label}</Caption>
              </Box>
            ) : (
              <Box
                padding={{horizontal: 24, vertical: 16}}
                border={{side: 'bottom', width: 1, color: ColorsWIP.KeylineGray}}
              >
                <Subheading>{label}</Subheading>
              </Box>
            )}
            <Box padding={{horizontal: 24, vertical: 16}}>
              <AssetValueGraph
                label={label}
                width="100%"
                data={graphDataByMetadataLabel[label]}
                xHover={xHover}
                onHoverX={(x) => x !== xHover && setXHover(x)}
              />
            </Box>
          </Box>
        ))}
      </div>
      {props.xAxis === 'partition' && (
        <Box padding={{vertical: 16, horizontal: 24}} style={{color: ColorsWIP.Gray400}}>
          When graphing values by partition, the highest data point for each materialized event
          label is displayed.
        </Box>
      )}
    </>
  );
};

/**
 * Helper function that iterates over the asset materializations and assembles time series data
 * and stats for all numeric metadata entries. This function makes the following guaruntees:
 *
 * - If a metadata entry is sparsely emitted, points are still included for missing x values
 *   with y = NaN. (For compatiblity with react-chartjs-2)
 * - If a metadata entry is generated many times for the same partition, and xAxis = partition,
 *   the MAX value emitted is used as the data point.
 *
 * Assumes that the data is pre-sorted in ascending partition order if using xAxis = partition.
 */
const extractNumericData = (datapoints: MaterializationGroup[], xAxis: 'time' | 'partition') => {
  const series: {
    [metadataEntryLabel: string]: AssetValueGraphData;
  } = {};

  // Build a set of the numeric metadata entry labels (note they may be sparsely emitted)
  const numericMetadataLabels = uniq(
    flatMap(datapoints, (e) =>
      (e.latest?.metadataEntries || [])
        .filter((k) => ['EventIntMetadataEntry', 'EventFloatMetadataEntry'].includes(k.__typename))
        .map((k) => k.label),
    ),
  );

  const append = (label: string, {x, y}: {x: number | string; y: number}) => {
    series[label] = series[label] || {minX: 0, maxX: 0, minY: 0, maxY: 0, values: [], xAxis};

    if (xAxis === 'partition') {
      // If the xAxis is partition keys, the graph may only contain one value for each partition.
      // If the existing sample for the partition was null, replace it. Otherwise take the
      // most recent value.
      const existingForPartition = series[label].values.find((v) => v.x === x);
      if (existingForPartition) {
        if (!isNaN(y)) {
          existingForPartition.y = y;
        }
        return;
      }
    }
    series[label].values.push({
      xNumeric: typeof x === 'number' ? x : series[label].values.length,
      x,
      y,
    });
  };

  for (const {partition, latest} of datapoints) {
    const x = (xAxis === 'partition' ? partition : Number(latest?.timestamp)) || null;

    if (x === null) {
      // exclude materializations where partition = null from partitioned graphs
      continue;
    }

    // Add an entry for every numeric metadata label
    for (const label of numericMetadataLabels) {
      const entry = latest?.metadataEntries.find((l) => l.label === label);
      if (!entry) {
        append(label, {x, y: NaN});
        continue;
      }

      let y = NaN;
      if (entry.__typename === 'EventIntMetadataEntry') {
        if (entry.intValue !== null) {
          y = entry.intValue;
        } else {
          // will incur precision loss here
          y = parseInt(entry.intRepr);
        }
      }
      if (entry.__typename === 'EventFloatMetadataEntry' && entry.floatValue !== null) {
        y = entry.floatValue;
      }

      append(label, {x, y});
    }

    // Add step execution time as a custom dataset
    const {startTime, endTime} = latest?.stepStats || {};
    append(LABEL_STEP_EXECUTION_TIME, {x, y: endTime && startTime ? endTime - startTime : NaN});
  }

  for (const serie of Object.values(series)) {
    const xs = serie.values.map((v) => v.xNumeric);
    const ys = serie.values.map((v) => v.y).filter((v) => !isNaN(v));
    serie.minXNumeric = Math.min(...xs);
    serie.maxXNumeric = Math.max(...xs);
    serie.minY = Math.min(...ys);
    serie.maxY = Math.max(...ys);
  }
  return series;
};

const ASSET_MATERIALIZATIONS_QUERY = gql`
  query AssetMaterializationsQuery(
    $assetKey: AssetKeyInput!
    $limit: Int
    $before: String
    $partitionInLast: Int
  ) {
    assetOrError(assetKey: $assetKey) {
      ... on Asset {
        id
        key {
          path
        }

        assetMaterializations(
          limit: $limit
          beforeTimestampMillis: $before
          partitionInLast: $partitionInLast
        ) {
          ...AssetMaterializationFragment
        }

        definition {
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
    stepStats {
      endTime
      startTime
    }
    label
    description
    metadataEntries {
      ...MetadataEntryFragment
    }
    assetLineage {
      ...AssetLineageFragment
    }
  }
  ${METADATA_ENTRY_FRAGMENT}
  ${ASSET_LINEAGE_FRAGMENT}
`;
