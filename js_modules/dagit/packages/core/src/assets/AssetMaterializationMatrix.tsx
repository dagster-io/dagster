import {Button} from '@blueprintjs/core';
import flatMap from 'lodash/flatMap';
import uniq from 'lodash/uniq';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {formatElapsedTime} from '../app/Util';
import {Timestamp} from '../app/time/Timestamp';
import {useViewport} from '../gantt/useViewport';
import {
  GridColumn,
  GridFloatingContainer,
  GridScrollContainer,
  LeftLabel,
} from '../partitions/RunMatrixUtils';
import {MetadataEntry} from '../runs/MetadataEntry';
import {titleForRun} from '../runs/RunUtils';
import {MetadataEntryFragment} from '../runs/types/MetadataEntryFragment';
import {ColorsWIP} from '../ui/Colors';
import {FontFamily} from '../ui/styles';

import {AssetPredecessorLink} from './AssetMaterializationTable';
import {Sparkline} from './Sparkline';
import {AssetNumericHistoricalData} from './types';
import {AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations} from './types/AssetMaterializationsQuery';
import {HistoricalMaterialization} from './useMaterializationBuckets';

const COL_WIDTH = 120;

const OVERSCROLL = 150;

export const LABEL_STEP_EXECUTION_TIME = 'Step Execution Time';

interface AssetMaterializationMatrixProps {
  materializations: HistoricalMaterialization[];
  isPartitioned: boolean;
  xAxis: 'time' | 'partition';
  xHover: number | string | null;
  onHoverX: (x: number | string | null) => void;
  graphDataByMetadataLabel: AssetNumericHistoricalData;
  graphedLabels: string[];
  setGraphedLabels: (labels: string[]) => void;
}

function xForAssetMaterialization(
  am: AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations,
  xAxis: 'time' | 'partition',
) {
  return xAxis === 'time' ? Number(am.materializationEvent.timestamp) : am.partition;
}

const EMPTY_CELL_DASH = <span style={{opacity: 0.3}}> - </span>;

export const AssetMaterializationMatrix: React.FC<AssetMaterializationMatrixProps> = ({
  materializations,
  isPartitioned,
  xAxis,
  xHover,
  onHoverX,
  graphDataByMetadataLabel,
  graphedLabels,
  setGraphedLabels,
}) => {
  const [hoveredLabel, setHoveredLabel] = React.useState<string>('');
  const {viewport, containerProps, onMoveToViewport} = useViewport({
    initialOffset: React.useCallback((el) => ({left: el.scrollWidth - el.clientWidth, top: 0}), []),
  });

  const anyPredecessors = materializations.some(({predecessors}) => !!predecessors?.length);

  const visibleRangeStart = Math.max(0, Math.floor((viewport.left - OVERSCROLL) / COL_WIDTH));
  const visibleCount = Math.ceil((viewport.width + OVERSCROLL * 2) / COL_WIDTH);
  const visible = materializations.slice(visibleRangeStart, visibleRangeStart + visibleCount);

  const lastXHover = React.useRef<string | number | null>(null);
  React.useEffect(() => {
    if (lastXHover.current === xHover) {
      return;
    }
    if (xHover !== null) {
      const idx = materializations.findIndex(
        (m) => xForAssetMaterialization(m.latest, xAxis) === xHover,
      );
      if ((idx !== -1 && idx < visibleRangeStart) || idx > visibleRangeStart + visibleCount) {
        onMoveToViewport({left: idx * COL_WIDTH - (viewport.width - COL_WIDTH) / 2, top: 0}, false);
      }
    }
    lastXHover.current = xHover;
  });

  const metadataLabels = uniq(
    flatMap(materializations, (m) =>
      m.latest.materializationEvent.materialization.metadataEntries.map((e) => e.label),
    ),
  );

  return (
    <PartitionRunMatrixContainer>
      <div
        style={{position: 'relative', display: 'flex', border: `1px solid ${ColorsWIP.Gray200}`}}
      >
        <GridFloatingContainer floating={true} style={{width: 300}}>
          <GridColumn disabled style={{width: 300, overflow: 'hidden'}}>
            {isPartitioned && <HeaderRowLabel>Partition</HeaderRowLabel>}
            <HeaderRowLabel>Run</HeaderRowLabel>
            <HeaderRowLabel>Timestamp</HeaderRowLabel>
            {anyPredecessors ? <HeaderRowLabel>Previous materializations</HeaderRowLabel> : null}
            {[...metadataLabels, LABEL_STEP_EXECUTION_TIME].map((label, idx) => (
              <MetadataRowLabel
                bordered={idx === 0 || label === LABEL_STEP_EXECUTION_TIME}
                key={label}
                label={label}
                hovered={label === hoveredLabel}
                graphData={graphDataByMetadataLabel[label]}
                graphEnabled={graphedLabels.includes(label)}
                onToggleGraphEnabled={() =>
                  setGraphedLabels(
                    graphedLabels.includes(label)
                      ? graphedLabels.filter((l) => l !== label)
                      : [...graphedLabels, label],
                  )
                }
              />
            ))}
          </GridColumn>
        </GridFloatingContainer>
        <GridScrollContainer {...containerProps}>
          <div
            style={{
              width: materializations.length * COL_WIDTH,
              position: 'relative',
              height: 80,
            }}
          >
            {visible.map((historicalMaterialization, visibleIdx) => {
              const {latest: assetMaterialization, predecessors} = historicalMaterialization;
              const {materializationEvent, partition} = assetMaterialization;
              const x = xForAssetMaterialization(assetMaterialization, xAxis);
              const {startTime, endTime} = materializationEvent.stepStats || {};

              const runId =
                assetMaterialization.runOrError.__typename === 'PipelineRun'
                  ? assetMaterialization.runOrError.runId
                  : '';

              return (
                <GridColumn
                  key={materializationEvent.timestamp}
                  onMouseEnter={() => onHoverX(x)}
                  hovered={xHover === x}
                  style={{
                    width: COL_WIDTH,
                    position: 'absolute',
                    zIndex: visible.length - visibleIdx,
                    left: (visibleIdx + visibleRangeStart) * COL_WIDTH,
                  }}
                >
                  {isPartitioned && <div className="cell">{partition}</div>}
                  <div className="cell" style={{fontFamily: FontFamily.monospace}}>
                    <Link
                      style={{marginRight: 5}}
                      to={`/instance/runs/${runId}?timestamp=${materializationEvent.timestamp}`}
                    >
                      {titleForRun({runId})}
                    </Link>
                  </div>
                  <div
                    className="cell"
                    style={anyPredecessors ? {} : {borderBottom: `1px solid ${ColorsWIP.Gray200}`}}
                  >
                    <Timestamp timestamp={{ms: Number(materializationEvent.timestamp)}} />
                  </div>
                  {anyPredecessors ? (
                    <div className="cell" style={{borderBottom: `1px solid ${ColorsWIP.Gray200}`}}>
                      {predecessors?.length ? (
                        <AssetPredecessorLink
                          isPartitioned={isPartitioned}
                          hasLineage={false}
                          predecessors={predecessors}
                        />
                      ) : null}
                    </div>
                  ) : null}
                  {metadataLabels.map((label) => {
                    const entry = materializationEvent.materialization.metadataEntries.find(
                      (m) => m.label === label,
                    );
                    return (
                      <div
                        key={label}
                        className="cell"
                        style={{width: COL_WIDTH}}
                        data-tooltip={plaintextFor(entry) || undefined}
                        onMouseEnter={() => setHoveredLabel(label)}
                        onMouseLeave={() => setHoveredLabel('')}
                      >
                        {entry ? <MetadataEntry entry={entry} /> : EMPTY_CELL_DASH}
                      </div>
                    );
                  })}
                  <div
                    className="cell"
                    style={{borderTop: `1px solid ${ColorsWIP.Gray200}`}}
                    onMouseEnter={() => setHoveredLabel(LABEL_STEP_EXECUTION_TIME)}
                    onMouseLeave={() => setHoveredLabel('')}
                  >
                    {endTime && startTime
                      ? formatElapsedTime((endTime - startTime) * 1000)
                      : EMPTY_CELL_DASH}
                  </div>
                </GridColumn>
              );
            })}
          </div>
        </GridScrollContainer>
      </div>
      {visible.length === 0 && <EmptyMessage>No data to display.</EmptyMessage>}
    </PartitionRunMatrixContainer>
  );
};

const HeaderRowLabel = styled(LeftLabel)`
  padding-left: 6px;
  color: ${ColorsWIP.Gray500};
`;

const MetadataRowLabel: React.FunctionComponent<{
  bordered?: boolean;
  label: string;
  hovered: boolean;
  graphEnabled: boolean;
  graphData?: AssetNumericHistoricalData[0];
  onToggleGraphEnabled: () => void;
}> = ({bordered, label, hovered, graphEnabled, graphData, onToggleGraphEnabled}) => (
  <LeftLabel
    key={label}
    hovered={hovered}
    data-tooltip={label}
    style={{display: 'flex', borderTop: bordered ? `1px solid ${ColorsWIP.Gray200}` : ''}}
  >
    <div style={{width: 149, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>
      <Button
        minimal
        small
        disabled={!graphData}
        onClick={onToggleGraphEnabled}
        icon={graphData ? (graphEnabled ? 'eye-open' : 'eye-off') : 'blank'}
      />
      {label}
    </div>
    {graphData && <Sparkline data={graphData} width={150} height={23} />}
  </LeftLabel>
);

const plaintextFor = (entry: MetadataEntryFragment | undefined) => {
  if (!entry) {
    return '';
  }
  if (entry.__typename === 'EventFloatMetadataEntry') {
    return entry.floatValue;
  } else if (entry.__typename === 'EventIntMetadataEntry') {
    if (entry.intValue !== null) {
      return entry.intValue.toLocaleString();
    }
    return entry.intRepr;
  } else if (entry.__typename === 'EventPathMetadataEntry') {
    return entry.path;
  } else if (entry.__typename === 'EventTextMetadataEntry') {
    return entry.text;
  } else if (entry.__typename === 'EventUrlMetadataEntry') {
    return entry.url;
  } else {
    return '';
  }
};

const EmptyMessage = styled.div`
  padding: 20px;
  text-align: center;
`;

const PartitionRunMatrixContainer = styled.div`
  display: block;
  margin-bottom: 20px;
`;
