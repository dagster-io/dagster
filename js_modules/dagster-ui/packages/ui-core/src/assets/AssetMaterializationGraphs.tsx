import {Box, Caption, Colors, Subheading} from '@dagster-io/ui-components';
import flatMap from 'lodash/flatMap';
import uniq from 'lodash/uniq';
import {useMemo, useState} from 'react';

import {AssetValueGraph, AssetValueGraphData} from './AssetValueGraph';
import {AssetMaterializationFragment} from './useRecentAssetEvents';

type GraphedEvent = {
  timestamp?: string;
  metadataEntries: AssetMaterializationFragment['metadataEntries'];
};

type GraphedGroup = {
  latest: GraphedEvent | null;
  all: GraphedEvent[];
  timestamp?: string;
  partition?: string;
};

export const AssetMaterializationGraphs = (props: {
  groups: GraphedGroup[];
  xAxis: 'partition' | 'time';
  asSidebarSection?: boolean;
  columnCount?: number;
  emptyState?: React.ReactNode;
}) => {
  const [xHover, setXHover] = useState<string | number | null>(null);

  const reversed = useMemo(() => {
    return [...props.groups].reverse();
  }, [props.groups]);

  const graphDataByMetadataLabel = extractNumericData(reversed, props.xAxis);
  const graphLabels = Object.keys(graphDataByMetadataLabel).slice(0, 100).sort();

  if (process.env.NODE_ENV === 'test') {
    return <span />; // chartjs and our useViewport hook don't play nicely with jest
  }

  const columns = props.columnCount || 2;

  return (
    <>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: `1fr `.repeat(columns),
          justifyContent: 'stretch',
        }}
      >
        {graphLabels.map((label) => (
          <Box key={label} style={{width: '100%'}}>
            <Box style={{width: '100%'}}>
              {props.asSidebarSection ? (
                <Box padding={{horizontal: 24, top: 8}} flex={{justifyContent: 'space-between'}}>
                  <Caption style={{fontWeight: 700}}>{label}</Caption>
                </Box>
              ) : (
                <Box padding={{vertical: 16}} flex={{justifyContent: 'space-between'}}>
                  <Subheading>{label}</Subheading>
                </Box>
              )}
              <Box padding={8}>
                <AssetValueGraph
                  label={label}
                  width="100%"
                  data={graphDataByMetadataLabel[label]!}
                  xHover={xHover}
                  onHoverX={(x) => x !== xHover && setXHover(x)}
                />
              </Box>
            </Box>
          </Box>
        ))}
      </div>
      {graphLabels.length === 0
        ? props.emptyState || (
            <Box
              margin={{horizontal: 24, vertical: 12}}
              style={{color: Colors.textLight(), fontSize: '0.8rem'}}
            >
              No numeric metadata entries available to be graphed.
            </Box>
          )
        : props.xAxis === 'partition' && (
            <Box padding={{vertical: 16, horizontal: 24}} style={{color: Colors.textLight()}}>
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
const extractNumericData = (datapoints: GraphedGroup[], xAxis: 'time' | 'partition') => {
  const series: {
    [metadataEntryLabel: string]: AssetValueGraphData;
  } = {};

  // Build a set of the numeric metadata entry labels (note they may be sparsely emitted)
  const numericMetadataLabels = uniq(
    flatMap(datapoints, (e) =>
      (e.latest?.metadataEntries || [])
        .filter((k) => ['IntMetadataEntry', 'FloatMetadataEntry'].includes(k.__typename))
        .map((k) => k.label),
    ),
  );

  const append = (label: string, {x, y}: {x: number | string; y: number}) => {
    const target: AssetValueGraphData = series[label] || {
      minY: 0,
      maxY: 0,
      minXNumeric: 0,
      maxXNumeric: 0,
      values: [],
      xAxis,
    };

    if (xAxis === 'partition') {
      // If the xAxis is partition keys, the graph may only contain one value for each partition.
      // If the existing sample for the partition was null, replace it. Otherwise take the
      // most recent value.
      const existingForPartition = target.values.find((v) => v.x === x);
      if (existingForPartition) {
        if (!isNaN(y)) {
          existingForPartition.y = y;
        }
        return;
      }
    }
    target.values.push({
      xNumeric: typeof x === 'number' ? x : target.values.length,
      x,
      y,
    });

    series[label] = target;
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
      if (entry.__typename === 'IntMetadataEntry') {
        if (entry.intValue !== null) {
          y = entry.intValue;
        } else {
          // will incur precision loss here
          y = parseInt(entry.intRepr);
        }
      }
      if (entry.__typename === 'FloatMetadataEntry' && entry.floatValue !== null) {
        y = entry.floatValue;
      }
      append(label, {x, y});
    }
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
