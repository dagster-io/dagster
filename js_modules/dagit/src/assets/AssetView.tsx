import {gql, useQuery} from '@apollo/client';
import {Button, Tab, Tabs, ButtonGroup, Colors} from '@blueprintjs/core';
import flatMap from 'lodash/flatMap';
import uniq from 'lodash/uniq';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {Timestamp} from 'src/app/time/Timestamp';
import {AssetMaterializationMatrix} from 'src/assets/AssetMaterializationMatrix';
import {AssetMaterializationTable} from 'src/assets/AssetMaterializationTable';
import {AssetValueGraph} from 'src/assets/AssetValueGraph';
import {
  AssetQuery,
  AssetQueryVariables,
  AssetQuery_assetOrError_Asset_assetMaterializations,
  AssetQuery_assetOrError_Asset,
} from 'src/assets/types/AssetQuery';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {useQueryPersistedState} from 'src/hooks/useQueryPersistedState';
import {MetadataEntry, METADATA_ENTRY_FRAGMENT} from 'src/runs/MetadataEntry';
import {titleForRun} from 'src/runs/RunUtils';
import {Group} from 'src/ui/Group';
import {Loading} from 'src/ui/Loading';
import {MetadataTable} from 'src/ui/MetadataTable';
import {Heading, Subheading} from 'src/ui/Text';
import {FontFamily} from 'src/ui/styles';

interface AssetKey {
  path: string[];
}

export const LABEL_STEP_EXECUTION_TIME = 'Step Execution Time';

export const AssetView: React.FunctionComponent<{assetKey: AssetKey}> = ({assetKey}) => {
  const assetPath = assetKey.path.join(' \u203A ');
  useDocumentTitle(`Asset: ${assetPath}`);

  const queryResult = useQuery<AssetQuery, AssetQueryVariables>(ASSET_QUERY, {
    variables: {assetKey: {path: assetKey.path}},
  });

  return (
    <Loading queryResult={queryResult}>
      {({assetOrError}) => {
        if (assetOrError.__typename !== 'Asset') {
          return null;
        }
        if (!assetOrError.assetMaterializations.length) {
          return <p>This asset has never been materialized.</p>;
        }
        return <AssetViewWithData asset={assetOrError} />;
      }}
    </Loading>
  );
};

const AssetViewWithData: React.FunctionComponent<{asset: AssetQuery_assetOrError_Asset}> = ({
  asset,
}) => {
  const [xHover, setXHover] = React.useState<string | number | null>(null);
  const [activeTab = 'graphs', setActiveTab] = useQueryPersistedState<'graphs' | 'list'>({
    queryKey: 'tab',
  });
  const [xAxis = 'time', setXAxis] = useQueryPersistedState<'partition' | 'time'>({
    queryKey: 'axis',
  });

  // Note: We want to show partition columns / options as soon as the user adds a partition,
  // even if previous materializations have partition=null, so this is determined here and passed
  // down through the component tree.
  const isPartitioned = asset.assetMaterializations.some((m) => m.partition);

  const assetMaterializations = [...asset.assetMaterializations].sort(
    (a, b) =>
      (xAxis === 'partition' && (a.partition || '').localeCompare(b.partition || '')) ||
      Number(a.materializationEvent.timestamp) - Number(b.materializationEvent.timestamp),
  );

  const graphDataByMetadataLabel = extractNumericData(assetMaterializations, xAxis);
  const [graphedLabels, setGraphedLabels] = React.useState(() =>
    Object.keys(graphDataByMetadataLabel).slice(0, 4),
  );

  const latest = asset.assetMaterializations[0];
  const latestEvent = latest && latest.materializationEvent;

  return (
    <div>
      <Group direction="column" spacing={12}>
        <Heading>{asset.key.path[asset.key.path.length - 1]}</Heading>
        <MetadataTable
          rows={[
            latest.partition
              ? {
                  key: 'Latest partition',
                  value: latest ? latest.partition : 'No materialization events',
                }
              : undefined,
            {
              key: 'Latest run',
              value: latest ? (
                <>
                  <Link
                    style={{fontFamily: FontFamily.monospace}}
                    to={`/instance/runs/${latestEvent.runId}?timestamp=${latestEvent.timestamp}`}
                  >
                    {titleForRun({runId: latestEvent.runId})}
                  </Link>
                  <span> at </span>
                  <Timestamp ms={Number(latestEvent.timestamp)} />
                </>
              ) : (
                'No materialization events'
              ),
            },
            ...latestEvent?.materialization.metadataEntries.map((entry) => ({
              key: entry.label,
              value: <MetadataEntry entry={entry} />,
            })),
          ].filter(Boolean)}
        />
      </Group>

      <div style={{display: 'flex', marginTop: 20}}>
        <Subheading>Materializations over Time</Subheading>
        <div style={{flex: 1}} />
        <ButtonGroup>
          <Button active={xAxis === 'time'} onClick={() => setXAxis('time')}>
            By Timestamp
          </Button>
          <Button
            active={xAxis === 'partition'}
            onClick={() => setXAxis('partition')}
            disabled={!isPartitioned}
          >
            By Partition
          </Button>
        </ButtonGroup>
      </div>

      <Tabs
        large={false}
        selectedTabId={activeTab}
        onChange={(t) => setActiveTab(t as 'graphs' | 'list')}
      >
        <Tab id="graphs" title="Graphs" />
        <Tab id="list" title="List" />
      </Tabs>

      {activeTab === 'list' ? (
        <AssetMaterializationTable
          isPartitioned={isPartitioned}
          materializations={[...assetMaterializations].reverse()}
        />
      ) : (
        <>
          <AssetMaterializationMatrix
            isPartitioned={isPartitioned}
            materializations={assetMaterializations}
            xAxis={xAxis}
            xHover={xHover}
            onHoverX={(x) => x !== xHover && setXHover(x)}
            graphDataByMetadataLabel={graphDataByMetadataLabel}
            graphedLabels={graphedLabels}
            setGraphedLabels={setGraphedLabels}
          />
          <div style={{display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between'}}>
            {[...graphedLabels].sort().map((label) => (
              <AssetValueGraph
                key={label}
                label={label}
                width={graphedLabels.length === 1 ? '100%' : '48%'}
                data={graphDataByMetadataLabel[label]}
                xHover={xHover}
                onHoverX={(x) => x !== xHover && setXHover(x)}
              />
            ))}
          </div>
          {xAxis === 'partition' && (
            <div style={{color: Colors.GRAY3, fontSize: '0.85rem'}}>
              When graphing values by partition, the highest data point for each materialized event
              label is displayed.
            </div>
          )}
        </>
      )}
    </div>
  );
};

const ASSET_QUERY = gql`
  query AssetQuery($assetKey: AssetKeyInput!) {
    assetOrError(assetKey: $assetKey) {
      ... on Asset {
        key {
          path
        }
        assetMaterializations(limit: 200) {
          partition
          runOrError {
            ... on PipelineRun {
              id
              runId
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
          }
        }
      }
    }
  }
  ${METADATA_ENTRY_FRAGMENT}
`;

export interface AssetNumericHistoricalData {
  [metadataEntryLabel: string]: {
    minY: number;
    maxY: number;
    minXNumeric: number;
    maxXNumeric: number;
    xAxis: 'time' | 'partition';
    values: {
      x: number | string; // time or partition
      xNumeric: number; // time or partition index
      y: number;
    }[];
  };
}

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
function extractNumericData(
  assetMaterializations: AssetQuery_assetOrError_Asset_assetMaterializations[],
  xAxis: 'time' | 'partition',
) {
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
      // If the existing sample for the partition was null, replace it. Otherwise take the max.
      // (We need some sort of approach, might as well make it deterministic.)
      const existingForPartition = series[label].values.find((v) => v.x === x);
      if (existingForPartition) {
        if (!isNaN(y)) {
          existingForPartition.y = existingForPartition.y ? Math.max(existingForPartition.y, y) : y;
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

      const y =
        entry.__typename === 'EventIntMetadataEntry'
          ? entry.intValue
          : entry.__typename === 'EventFloatMetadataEntry'
          ? entry.floatValue
          : NaN; // should only happen if data type of entry has changed in the graphed period

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
}
