import {Colors, Button} from '@blueprintjs/core';
import flatMap from 'lodash/flatMap';
import uniq from 'lodash/uniq';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {formatElapsedTime} from 'src/app/Util';
import {Timestamp} from 'src/app/time/Timestamp';
import {AssetNumericHistoricalData, LABEL_STEP_EXECUTION_TIME} from 'src/assets/AssetView';
import {Sparkline} from 'src/assets/Sparkline';
import {
  AssetQuery_assetOrError_Asset_assetMaterializations,
  AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries,
} from 'src/assets/types/AssetQuery';
import {useViewport} from 'src/gantt/useViewport';
import {
  GridColumn,
  GridScrollContainer,
  GridFloatingContainer,
  LeftLabel,
} from 'src/partitions/RunMatrixUtils';
import {MetadataEntry} from 'src/runs/MetadataEntry';
import {titleForRun} from 'src/runs/RunUtils';
import {FontFamily} from 'src/ui/styles';

const COL_WIDTH = 120;

const OVERSCROLL = 150;

interface AssetMaterializationMatrixProps {
  materializations: AssetQuery_assetOrError_Asset_assetMaterializations[];
  isPartitioned: boolean;
  xAxis: 'time' | 'partition';
  xHover: number | string | null;
  onHoverX: (x: number | string | null) => void;
  graphDataByMetadataLabel: AssetNumericHistoricalData;
  graphedLabels: string[];
  setGraphedLabels: (labels: string[]) => void;
}

function xForAssetMaterialization(
  am: AssetQuery_assetOrError_Asset_assetMaterializations,
  xAxis: 'time' | 'partition',
) {
  return xAxis === 'time' ? Number(am.materializationEvent.timestamp) : am.partition;
}

const EMPTY_CELL_DASH = <span style={{opacity: 0.3}}> - </span>;

export const AssetMaterializationMatrix: React.FunctionComponent<AssetMaterializationMatrixProps> = ({
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

  const visibleRangeStart = Math.max(0, Math.floor((viewport.left - OVERSCROLL) / COL_WIDTH));
  const visibleCount = Math.ceil((viewport.width + OVERSCROLL * 2) / COL_WIDTH);
  const visible = materializations.slice(visibleRangeStart, visibleRangeStart + visibleCount);

  const lastXHover = React.useRef<string | number | null>(null);
  React.useEffect(() => {
    if (lastXHover.current === xHover) {
      return;
    }
    if (xHover !== null) {
      const idx = materializations.findIndex((m) => xForAssetMaterialization(m, xAxis) === xHover);
      if ((idx !== -1 && idx < visibleRangeStart) || idx > visibleRangeStart + visibleCount) {
        onMoveToViewport({left: idx * COL_WIDTH - (viewport.width - COL_WIDTH) / 2, top: 0}, false);
      }
    }
    lastXHover.current = xHover;
  });

  const metadataLabels = uniq(
    flatMap(materializations, (m) =>
      m.materializationEvent.materialization.metadataEntries.map((e) => e.label),
    ),
  );

  return (
    <PartitionRunMatrixContainer>
      <div style={{position: 'relative', display: 'flex', border: `1px solid ${Colors.GRAY5}`}}>
        <GridFloatingContainer floating={true} style={{width: 300}}>
          <GridColumn disabled style={{width: 300, overflow: 'hidden'}}>
            <HeaderRowLabel>Run</HeaderRowLabel>
            {isPartitioned && <HeaderRowLabel>Partition</HeaderRowLabel>}
            <HeaderRowLabel>Timestamp</HeaderRowLabel>
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
            {visible.map((assetMaterialization, visibleIdx) => {
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
                  <div className={`cell`} style={{fontFamily: FontFamily.monospace}}>
                    <Link
                      style={{marginRight: 5}}
                      to={`/instance/runs/${runId}?timestamp=${materializationEvent.timestamp}`}
                    >
                      {titleForRun({runId})}
                    </Link>
                  </div>
                  {isPartitioned && <div className={`cell`}>{partition}</div>}
                  <div className={`cell`} style={{borderBottom: `1px solid ${Colors.LIGHT_GRAY1}`}}>
                    <Timestamp ms={Number(materializationEvent.timestamp)} />
                  </div>
                  {metadataLabels.map((label) => {
                    const entry = materializationEvent.materialization.metadataEntries.find(
                      (m) => m.label === label,
                    );
                    return (
                      <div
                        key={label}
                        className={`cell`}
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
                    className={`cell`}
                    style={{borderTop: `1px solid ${Colors.LIGHT_GRAY1}`}}
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
  color: ${Colors.GRAY2};
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
    style={{display: 'flex', borderTop: bordered ? `1px solid ${Colors.LIGHT_GRAY1}` : ''}}
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

const plaintextFor = (
  entry:
    | AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries
    | undefined,
) => {
  if (!entry) {
    return '';
  }
  if (entry.__typename === 'EventFloatMetadataEntry') {
    return entry.floatValue;
  } else if (entry.__typename === 'EventIntMetadataEntry') {
    return entry.intValue.toLocaleString();
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
