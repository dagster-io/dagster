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
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {IconWIP, IconWrapper} from '../ui/Icon';
import {FontFamily} from '../ui/styles';

import {AssetPredecessorLink} from './AssetMaterializationTable';
import {Sparkline} from './Sparkline';
import {AssetNumericHistoricalData} from './types';
import {AssetMaterializationFragment} from './types/AssetMaterializationFragment';
import {HistoricalMaterialization} from './useMaterializationBuckets';

const COL_WIDTH = 240;

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

function xForAssetMaterialization(am: AssetMaterializationFragment, xAxis: 'time' | 'partition') {
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
            <Box
              padding={{vertical: 4}}
              border={{side: 'bottom', width: 1, color: ColorsWIP.KeylineGray}}
            />
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
                assetMaterialization.runOrError.__typename === 'Run'
                  ? assetMaterialization.runOrError.runId
                  : '';

              return (
                <AssetGridColumn
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
                  <div className="cell">
                    <Timestamp timestamp={{ms: Number(materializationEvent.timestamp)}} />
                  </div>
                  {anyPredecessors ? (
                    <div className="cell">
                      {predecessors?.length ? (
                        <AssetPredecessorLink
                          isPartitioned={isPartitioned}
                          hasLineage={false}
                          predecessors={predecessors}
                        />
                      ) : null}
                    </div>
                  ) : null}
                  <AssetGridColumnSpacer />
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
                </AssetGridColumn>
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
  padding: 4px 24px;
  color: ${ColorsWIP.Gray700};
  height: 32px;
  box-shadow: ${ColorsWIP.KeylineGray} 0 -1px 0 inset;
`;

const MetadataRowLabel: React.FunctionComponent<{
  bordered?: boolean;
  label: string;
  hovered: boolean;
  graphEnabled: boolean;
  graphData?: AssetNumericHistoricalData[0];
  onToggleGraphEnabled: () => void;
}> = ({label, hovered, graphEnabled, graphData, onToggleGraphEnabled}) => (
  <StyledMetadataRowLabel key={label} hovered={hovered} data-tooltip={label}>
    {graphData ? (
      <VisibilityButton disabled={!graphData} onClick={onToggleGraphEnabled}>
        <IconWIP name={graphEnabled ? 'visibility' : 'visibility_off'} />
      </VisibilityButton>
    ) : null}
    <div style={{width: 149, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>
      {label}
    </div>
    {graphData && <Sparkline data={graphData} width={150} height={23} />}
  </StyledMetadataRowLabel>
);

const StyledMetadataRowLabel = styled(LeftLabel)`
  display: flex;
  align-items: center;
  border: none;
  color: ${ColorsWIP.Gray700};
  height: 32px;
  padding: 8px 0 8px 24px;
  position: relative;
  box-shadow: ${ColorsWIP.KeylineGray} 0 -1px 0 inset;
`;

const VisibilityButton = styled.button`
  background-color: transparent;
  border: none;
  cursor: pointer;
  padding: 0;
  margin: 0;
  position: absolute;
  left: 4px;

  :focus,
  :active {
    outline: none;
  }

  ${IconWrapper} {
    transition: background-color 100ms;
  }

  :hover ${IconWrapper} {
    background-color: ${ColorsWIP.Gray900};
  }
`;

const AssetGridColumnSpacer = styled.div`
  padding: 4px 0;
  box-shadow: ${ColorsWIP.KeylineGray} 0 -1px 0 inset, ${ColorsWIP.KeylineGray} -1px 0 0 inset;
`;

const AssetGridColumn = styled(GridColumn)`
  width: 240px;

  .cell {
    height: 32px;
    padding: 8px;
    box-shadow: ${ColorsWIP.KeylineGray} 0 -1px 0 inset, ${ColorsWIP.KeylineGray} -1px 0 0 inset;
    font-family: ${FontFamily.monospace};
    font-size: 16px;
  }
`;

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
