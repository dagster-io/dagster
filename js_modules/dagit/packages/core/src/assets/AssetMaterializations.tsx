import {gql, useQuery} from '@apollo/client';
import flatMap from 'lodash/flatMap';
import uniq from 'lodash/uniq';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {SidebarSection} from '../pipelines/SidebarComponents';
import {METADATA_ENTRY_FRAGMENT} from '../runs/MetadataEntry';
import {Box} from '../ui/Box';
import {ButtonGroup} from '../ui/ButtonGroup';
import {ColorsWIP} from '../ui/Colors';
import {IconWIP} from '../ui/Icon';
import {NonIdealState} from '../ui/NonIdealState';
import {Spinner} from '../ui/Spinner';
import {Caption, Subheading} from '../ui/Text';
import {CurrentRunsBanner} from '../workspace/asset-graph/CurrentRunsBanner';
import {LiveDataForNode} from '../workspace/asset-graph/Utils';

import {ASSET_LINEAGE_FRAGMENT} from './AssetLineageElements';
import {AssetMaterializationTable} from './AssetMaterializationTable';
import {AssetValueGraph} from './AssetValueGraph';
import {AssetViewParams} from './AssetView';
import {LatestMaterializationMetadata} from './LastMaterializationMetadata';
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
  liveData?: LiveDataForNode;
  params: AssetViewParams;
  paramsTimeWindowOnly: boolean;
  setParams: (params: AssetViewParams) => void;

  // This timestamp is a "hint", when it changes this component will refetch
  // to retrieve new data. Just don't want to poll the entire table query.
  assetLastMaterializedAt: string | undefined;
}

const LABEL_STEP_EXECUTION_TIME = 'Step Execution Time';

export const AssetMaterializations: React.FC<Props> = ({
  assetKey,
  assetLastMaterializedAt,
  asSidebarSection,
  params,
  paramsTimeWindowOnly,
  setParams,
  liveData,
}) => {
  const {data, loading, refetch} = useQuery<
    AssetMaterializationsQuery,
    AssetMaterializationsQueryVariables
  >(ASSET_MATERIALIZATIONS_QUERY, {
    variables: {
      assetKey: {path: assetKey.path},
      before: paramsTimeWindowOnly && params.asOf ? `${Number(params.asOf) + 1}` : undefined,
      limit: 200,
    },
  });

  React.useEffect(() => {
    if (paramsTimeWindowOnly) {
      return;
    }
    refetch();
  }, [paramsTimeWindowOnly, assetLastMaterializedAt, refetch]);

  const asset = data?.assetOrError.__typename === 'Asset' ? data?.assetOrError : null;
  const materializations = asset?.assetMaterializations || [];
  const hasPartitions = materializations.some((m) => m.partition);
  const hasLineage = materializations.some((m) => m.materializationEvent.assetLineage.length > 0);

  const {xAxis = hasPartitions ? 'partition' : 'time', asOf} = params;
  const bucketed = useMaterializationBuckets({
    shouldBucketPartitions: xAxis === 'partition',
    materializations,
    hasPartitions,
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

  if (asSidebarSection) {
    const latest = materializations[0];
    return (
      <>
        <CurrentRunsBanner liveData={liveData} />
        <SidebarSection title={'Materialization in Last Run'}>
          <>
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
            <Box margin={{bottom: 12, horizontal: 12, top: 20}}>
              <AssetCatalogLink to={`/instance/assets/${assetKey.path.join('/')}`}>
                {'View All in Asset Catalog '}
                <IconWIP name="open_in_new" color={ColorsWIP.Blue500} />
              </AssetCatalogLink>
            </Box>
          </>
        </SidebarSection>
        <SidebarSection title={'Materialization Plots'}>
          <AssetMaterializationGraphs
            xAxis={xAxis}
            asSidebarSection
            assetMaterializations={reversed}
          />
        </SidebarSection>
      </>
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
                onClick={(id: string) => setParams({...params, xAxis: id as 'partition' | 'time'})}
              />
            </div>
          ) : null}
        </Box>
        <CurrentRunsBanner liveData={liveData} />
        <AssetMaterializationTable
          hasPartitions={hasPartitions}
          hasLineage={hasLineage}
          materializations={bucketed}
          focused={
            (bucketed.find((b) => Number(b.timestamp) <= Number(asOf)) || bucketed[0])?.timestamp
          }
          setFocused={(asOf) =>
            setParams({
              ...params,
              asOf: paramsTimeWindowOnly || asOf !== bucketed[0]?.timestamp ? asOf : undefined,
            })
          }
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
                width={'100%'}
                data={graphDataByMetadataLabel[label]}
                xHover={xHover}
                onHoverX={(x) => x !== xHover && setXHover(x)}
              />
            </Box>
          </Box>
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

const AssetCatalogLink = styled(Link)`
  display: flex;
  gap: 5px;
  align-items: center;
  justify-content: flex-end;
  margin-top: -10px;
`;
