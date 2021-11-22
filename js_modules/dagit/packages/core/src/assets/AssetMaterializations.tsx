import {gql, useQuery} from '@apollo/client';
import flatMap from 'lodash/flatMap';
import uniq from 'lodash/uniq';
import * as React from 'react';

import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {METADATA_ENTRY_FRAGMENT} from '../runs/MetadataEntry';
import {Box} from '../ui/Box';
import {ButtonGroup} from '../ui/ButtonGroup';
import {ColorsWIP} from '../ui/Colors';
import {NonIdealState} from '../ui/NonIdealState';
import {Spinner} from '../ui/Spinner';
import {Subheading} from '../ui/Text';

import {ASSET_LINEAGE_FRAGMENT} from './AssetLineageElements';
import {AssetMaterializationTable} from './AssetMaterializationTable';
import {AssetValueGraph} from './AssetValueGraph';
import {AssetKey, AssetNumericHistoricalData} from './types';
import {AssetMaterializationFragment} from './types/AssetMaterializationFragment';
import {
  AssetMaterializationsQuery,
  AssetMaterializationsQueryVariables,
} from './types/AssetMaterializationsQuery';
import {HistoricalMaterialization, useMaterializationBuckets} from './useMaterializationBuckets';

interface Props {
  assetKey: AssetKey;
  asSidebarSection?: boolean;
}
const LABEL_STEP_EXECUTION_TIME = 'Step Execution Time';

export const AssetMaterializations: React.FC<Props> = ({assetKey, asSidebarSection}) => {
  const {data, loading} = useQuery<AssetMaterializationsQuery, AssetMaterializationsQueryVariables>(
    ASSET_MATERIALIZATIONS_QUERY,
    {
      variables: {
        assetKey: {path: assetKey.path},
        limit: 200,
      },
    },
  );

  const asset = data?.assetOrError.__typename === 'Asset' ? data?.assetOrError : null;
  const assetMaterializations = asset?.assetMaterializations || [];
  const hasPartitions = assetMaterializations.some((m) => m.partition);
  const hasLineage = assetMaterializations.some(
    (m) => m.materializationEvent.assetLineage.length > 0,
  );

  const [{xAxis, asOf}, setParams] = useQueryPersistedState<{
    xAxis: 'partition' | 'time';
    asOf: string;
  }>({
    defaults: {xAxis: hasPartitions ? 'partition' : 'time'},
  });

  const bucketed = useMaterializationBuckets({
    materializations: assetMaterializations,
    hasPartitions,
    shouldBucketPartitions: xAxis === 'partition',
  });

  const reversed = React.useMemo(() => [...bucketed].reverse(), [bucketed]);
  const activeItems = React.useMemo(() => new Set([xAxis]), [xAxis]);

  if (process.env.NODE_ENV === 'test') {
    return <span />; // chartjs and our useViewport hook don't play nicely with jest
  }

  if (loading) {
    return (
      <Box padding={{vertical: 20}}>
        <Spinner purpose="section" />
      </Box>
    );
  }

  if (!reversed.length) {
    return (
      <Box padding={{vertical: 20}}>
        <NonIdealState
          icon="asset"
          title="No materializations"
          description="No materializations were found for this asset."
        />
      </Box>
    );
  }

  if (asSidebarSection) {
    return (
      <AssetMaterializationGraphs xAxis={xAxis} asSidebarSection assetMaterializations={reversed} />
    );
  }

  return (
    <Box style={{display: 'flex'}}>
      <Box style={{flex: 1}}>
        <Box
          flex={{justifyContent: 'space-between', alignItems: 'center'}}
          padding={{vertical: 16, horizontal: 24}}
          border={{side: 'top', width: 1, color: ColorsWIP.KeylineGray}}
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
                onClick={(id: string) => setParams({xAxis: id as 'partition' | 'time', asOf: asOf})}
              />
            </div>
          ) : null}
        </Box>
        <AssetMaterializationTable
          hasPartitions={hasPartitions}
          hasLineage={hasLineage}
          materializations={bucketed}
          focused={
            bucketed.find((b) => Number(b.latest.materializationEvent.timestamp) <= Number(asOf))
              ?.latest.materializationEvent.timestamp
          }
          setFocused={(asOf) => setParams({xAxis, asOf: asOf})}
        />
      </Box>
      <Box style={{width: '40%'}} border={{side: 'left', color: ColorsWIP.KeylineGray, width: 1}}>
        <AssetMaterializationGraphs
          xAxis={xAxis}
          asSidebarSection={asSidebarSection}
          assetMaterializations={reversed}
        />
      </Box>
    </Box>
  );
};

const AssetMaterializationGraphs: React.FC<{
  assetMaterializations: HistoricalMaterialization[];
  xAxis: 'partition' | 'time';
  asSidebarSection?: boolean;
}> = (props) => {
  const {assetMaterializations, xAxis} = props;
  const [xHover, setXHover] = React.useState<string | number | null>(null);
  const latest = assetMaterializations.map((m) => m.latest);

  const graphDataByMetadataLabel = extractNumericData(latest, xAxis);
  const [graphedLabels, setGraphedLabels] = React.useState(() =>
    Object.keys(graphDataByMetadataLabel).slice(0, 4),
  );

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
          <AssetValueGraph
            key={label}
            label={label}
            width={'100%'}
            data={graphDataByMetadataLabel[label]}
            xHover={xHover}
            onHoverX={(x) => x !== xHover && setXHover(x)}
          />
        ))}
      </div>
      {xAxis === 'partition' && (
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
const extractNumericData = (
  assetMaterializations: AssetMaterializationFragment[],
  xAxis: 'time' | 'partition',
) => {
  const series: AssetNumericHistoricalData = {};

  // Build a set of the numeric metadata entry labels (note they may be sparsely emitted)
  const numericMetadataLabels = uniq(
    flatMap(assetMaterializations, (e) =>
      e.materializationEvent.materialization.metadataEntries
        .filter(
          (k) =>
            k.__typename === 'EventIntMetadataEntry' || k.__typename === 'EventFloatMetadataEntry',
        )
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

  for (const {partition, materializationEvent} of assetMaterializations) {
    const x = xAxis === 'partition' ? partition : Number(materializationEvent.timestamp);
    if (x === null) {
      // exclude materializations where partition = null from partitioned graphs
      continue;
    }

    // Add an entry for every numeric metadata label
    for (const label of numericMetadataLabels) {
      const entry = materializationEvent.materialization.metadataEntries.find(
        (l) => l.label === label,
      );
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
    const {startTime, endTime} = materializationEvent.stepStats || {};
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
  query AssetMaterializationsQuery($assetKey: AssetKeyInput!, $limit: Int!, $before: String) {
    assetOrError(assetKey: $assetKey) {
      ... on Asset {
        id
        key {
          path
        }
        assetMaterializations(limit: $limit, beforeTimestampMillis: $before) {
          ...AssetMaterializationFragment
        }
      }
    }
  }
  fragment AssetMaterializationFragment on AssetMaterialization {
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
    materializationEvent {
      runId
      timestamp
      stepKey
      stepStats {
        endTime
        startTime
      }
      materialization {
        label
        description
        metadataEntries {
          ...MetadataEntryFragment
        }
      }
      assetLineage {
        ...AssetLineageFragment
      }
    }
  }
  ${METADATA_ENTRY_FRAGMENT}
  ${ASSET_LINEAGE_FRAGMENT}
`;
