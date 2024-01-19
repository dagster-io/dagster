import {gql, useQuery} from '@apollo/client';
import {
  Box,
  Button,
  Colors,
  Dialog,
  DialogFooter,
  Icon,
  Menu,
  MenuItem,
  Popover,
  useViewport,
} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

import {PartitionRunList} from './PartitionRunList';
import {
  BOX_SIZE,
  GridColumn,
  GridFloatingContainer,
  LeftLabel,
  TopLabel,
  TopLabelTilted,
  topLabelHeightForLabels,
} from './RunMatrixUtils';
import {
  PartitionStepStatusPipelineQuery,
  PartitionStepStatusPipelineQueryVariables,
} from './types/PartitionStepStatus.types';
import {PartitionMatrixStepRunFragment} from './types/useMatrixData.types';
import {
  MatrixData,
  MatrixStep,
  PARTITION_MATRIX_SOLID_HANDLE_FRAGMENT,
  PartitionRuns,
  StatusSquareColor,
  useMatrixData,
} from './useMatrixData';
import {GraphQueryItem} from '../app/GraphQueryImpl';
import {tokenForAssetKey} from '../asset-graph/Utils';
import {AssetPartitionStatus} from '../assets/AssetPartitionStatus';
import {
  PartitionHealthData,
  PartitionHealthDimension,
  Range,
  partitionStatusAtIndex,
} from '../assets/usePartitionHealthData';
import {GanttChartMode} from '../gantt/Constants';
import {buildLayout} from '../gantt/GanttChartLayout';
import {RunStatus} from '../graphql/types';
import {linkToRunEvent} from '../runs/RunUtils';
import {RunFilterToken} from '../runs/RunsFilterInput';
import {MenuLink} from '../ui/MenuLink';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

const BUFFER = 3;

export const getVisibleItemCount = (viewportWidth: number) =>
  Math.ceil(viewportWidth / BOX_SIZE) - BUFFER;

interface PartitionRunSelection {
  partitionName: string;
  stepName?: string;
}

interface PartitionStepStatusBaseProps {
  offset: number;
  setOffset: (val: number) => void;
  setPageSize: (val: number) => void;
  pipelineName: string;
  partitionNames: string[];

  runFilters?: RunFilterToken[];
  setRunFilters?: (val: RunFilterToken[]) => void;
}

const timeboundsOfPartitions = (partitionColumns: {steps: {unix: number}[]}[]) => {
  let [minUnix, maxUnix] = [Date.now() / 1000, 1];
  for (const partition of partitionColumns) {
    for (const step of partition.steps) {
      if (step.unix === 0) {
        continue;
      }
      [minUnix, maxUnix] = [Math.min(minUnix, step.unix), Math.max(maxUnix, step.unix)];
    }
  }
  return [minUnix, maxUnix] as const;
};

interface PartitionPerAssetStatusProps
  extends Omit<PartitionStepStatusBaseProps, 'partitionNames'> {
  assetHealth: PartitionHealthData[];
  assetQueryItems: GraphQueryItem[];
  rangeDimensionIdx: number;
  rangeDimension: PartitionHealthDimension;
}

export const PartitionPerAssetStatus = ({
  assetHealth,
  rangeDimension,
  rangeDimensionIdx,
  assetQueryItems,
  ...rest
}: PartitionPerAssetStatusProps) => {
  const rangesByAssetKey: {[assetKey: string]: Range[]} = {};
  for (const a of assetHealth) {
    if (a.dimensions[rangeDimensionIdx]?.name !== rangeDimension.name) {
      // Ignore assets in the job / graph that do not have the range partition dimension.
      continue;
    }
    const ranges = a.rangesForSingleDimension(rangeDimensionIdx);
    rangesByAssetKey[tokenForAssetKey(a.assetKey)] = ranges;
  }

  const layout = buildLayout({nodes: assetQueryItems, mode: GanttChartMode.FLAT});
  const layoutBoxesWithRangeDimension = layout.boxes.filter((b) => !!rangesByAssetKey[b.node.name]);

  const data: MatrixData = {
    stepRows: layoutBoxesWithRangeDimension.map((box) => ({
      x: box.x,
      name: box.node.name,
      totalFailurePercent: 0,
      finalFailurePercent: 0,
    })),
    partitions: [],
    partitionColumns: rangeDimension.partitionKeys.map((partitionKey, partitionKeyIdx) => ({
      idx: partitionKeyIdx,
      name: partitionKey,
      runsLoaded: true,
      runs: [],
      steps: layoutBoxesWithRangeDimension.map((box) => ({
        name: box.node.name,
        unix: 0,
        color: assetPartitionStatusToSquareColor(
          partitionStatusAtIndex(rangesByAssetKey[box.node.name]!, partitionKeyIdx),
        ),
      })),
    })),
  };

  return (
    <PartitionStepStatus
      {...rest}
      partitionNames={rangeDimension.partitionKeys}
      data={data}
      showLatestRun={false}
    />
  );
};

const assetPartitionStatusToSquareColor = (state: AssetPartitionStatus[]): StatusSquareColor => {
  return state.includes(AssetPartitionStatus.MATERIALIZED) &&
    state.includes(AssetPartitionStatus.MISSING)
    ? 'SUCCESS-MISSING'
    : state.includes(AssetPartitionStatus.MATERIALIZED)
    ? 'SUCCESS'
    : state.includes(AssetPartitionStatus.FAILED) && state.includes(AssetPartitionStatus.MISSING)
    ? 'FAILURE-MISSING'
    : state.includes(AssetPartitionStatus.FAILED)
    ? 'FAILURE'
    : 'MISSING';
};

interface PartitionPerOpStatusProps extends PartitionStepStatusBaseProps {
  repoAddress: RepoAddress;
  partitions: PartitionRuns[];
}

export const PartitionPerOpStatus = ({
  repoAddress,
  pipelineName,
  partitions,
  partitionNames,
  ...rest
}: PartitionPerOpStatusProps) => {
  // Retrieve the pipeline's structure
  const repositorySelector = repoAddressToSelector(repoAddress);
  const pipelineSelector = {...repositorySelector, pipelineName};
  const pipeline = useQuery<
    PartitionStepStatusPipelineQuery,
    PartitionStepStatusPipelineQueryVariables
  >(PARTITION_STEP_STATUS_PIPELINE_QUERY, {
    variables: {pipelineSelector},
  });

  const solidHandles =
    pipeline.data?.pipelineSnapshotOrError.__typename === 'PipelineSnapshot' &&
    pipeline.data.pipelineSnapshotOrError.solidHandles;

  const data = useMatrixData({
    partitionNames,
    partitions,
    stepQuery: '',
    solidHandles,
  });

  if (!data) {
    return <span />;
  }
  return (
    <PartitionStepStatus
      {...rest}
      showLatestRun={true}
      pipelineName={pipelineName}
      partitionNames={partitionNames}
      data={data}
    />
  );
};

interface PartitionStepStatusProps extends PartitionStepStatusBaseProps {
  data: MatrixData;
  showLatestRun: boolean;
}

const PartitionStepStatus = (props: PartitionStepStatusProps) => {
  const {viewport, containerProps} = useViewport();
  const [hovered, setHovered] = React.useState<PartitionRunSelection | null>(null);
  const [focused, setFocused] = React.useState<PartitionRunSelection | null>(null);
  const {setPageSize, data} = props;

  React.useEffect(() => {
    if (viewport.width) {
      setPageSize(getVisibleItemCount(viewport.width));
    }
  }, [viewport.width, setPageSize]);

  const {stepRows, partitionColumns} = data;

  const sortPartitionSteps = (steps: MatrixStep[]) => {
    const stepsByName = {};
    steps.forEach((step) => ((stepsByName as any)[step.name] = step));
    return stepRows.map((stepRow) => (stepsByName as any)[stepRow.name]);
  };

  const visibleCount = getVisibleItemCount(viewport.width);
  const visibleStart = Math.max(0, partitionColumns.length - props.offset - visibleCount);
  const visibleEnd = Math.max(visibleCount, partitionColumns.length - props.offset);
  const visibleColumns = partitionColumns.slice(visibleStart, visibleEnd);
  const [minUnix, maxUnix] = timeboundsOfPartitions(partitionColumns);
  const topLabelHeight = topLabelHeightForLabels(partitionColumns.map((p) => p.name));

  return (
    <PartitionRunMatrixContainer>
      <Dialog
        isOpen={!!focused}
        onClose={() => setFocused(null)}
        style={{width: '90vw'}}
        title={focused ? `${focused.partitionName} runs` : ''}
      >
        <Box padding={{bottom: 12}}>
          {focused && (
            <PartitionRunList
              pipelineName={props.pipelineName}
              partitionName={focused.partitionName}
            />
          )}
        </Box>
        <DialogFooter>
          <Button intent="primary" autoFocus={true} onClick={() => setFocused(null)}>
            OK
          </Button>
        </DialogFooter>
      </Dialog>
      <div
        style={{
          position: 'relative',
          display: 'flex',
        }}
      >
        <GridFloatingContainer floating={props.offset + visibleCount < props.partitionNames.length}>
          <GridColumn disabled style={{flex: 1, flexShrink: 1, overflow: 'hidden'}}>
            <TopLabel style={{height: topLabelHeight}} />
            {props.showLatestRun && <LeftLabel style={{paddingLeft: 24}}>Last Run</LeftLabel>}
            <Divider />
            {stepRows.map((step) => (
              <LeftLabel
                style={{paddingLeft: 8 + step.x}}
                key={step.name}
                data-tooltip={step.name}
                hovered={step.name === hovered?.stepName}
              >
                {step.name}
              </LeftLabel>
            ))}
          </GridColumn>
        </GridFloatingContainer>

        {props.offset + visibleCount < props.partitionNames.length ? (
          <PagerControl
            $direction="left"
            onClick={() =>
              props.setOffset(
                Math.max(
                  0,
                  Math.min(
                    props.offset + visibleCount - 1,
                    props.partitionNames.length - visibleCount,
                  ),
                ),
              )
            }
          >
            <Icon name="chevron_left" />
          </PagerControl>
        ) : null}
        <div style={{flex: 1, overflow: 'hidden', position: 'relative'}} {...containerProps}>
          <div
            style={{
              width: partitionColumns.length * BOX_SIZE,
              position: 'absolute',
              height: '100%',
              right: 0,
              zIndex: 1,
            }}
          >
            {visibleColumns.map((p, idx) => (
              <GridColumn
                key={p.name}
                style={{
                  zIndex: visibleColumns.length - idx,
                  width: BOX_SIZE,
                  position: 'absolute',
                  right: (visibleCount - idx) * BOX_SIZE + 20,
                }}
              >
                <TopLabelTilted $height={topLabelHeight} label={p.name} />
                {props.showLatestRun && (
                  <LeftLabel style={{textAlign: 'center'}}>
                    <PartitionSquare
                      key={`${p.name}:__full_status`}
                      runs={p.runs}
                      runsLoaded={p.runsLoaded}
                      minUnix={minUnix}
                      maxUnix={maxUnix}
                      hovered={hovered}
                      setHovered={setHovered}
                      setFocused={setFocused}
                      partitionName={p.name}
                    />
                  </LeftLabel>
                )}
                <Divider />
                {sortPartitionSteps(p.steps).map((s) => (
                  <PartitionSquare
                    key={s.name}
                    step={s}
                    runs={p.runs}
                    runsLoaded={p.runsLoaded}
                    minUnix={minUnix}
                    maxUnix={maxUnix}
                    hovered={hovered}
                    setHovered={setHovered}
                    setFocused={setFocused}
                    partitionName={p.name}
                  />
                ))}
              </GridColumn>
            ))}
          </div>
        </div>
        {props.offset > 0 ? (
          <PagerControl
            $direction="right"
            onClick={() => props.setOffset(Math.max(0, props.offset - visibleCount))}
          >
            <Icon name="chevron_right" />
          </PagerControl>
        ) : null}
      </div>
    </PartitionRunMatrixContainer>
  );
};

const PagerControl = styled.div<{$direction: 'left' | 'right'}>`
  width: 30px;
  position: absolute;
  border: 1px solid ${Colors.keylineDefault()};
  border-radius: 3px;
  display: flex;
  justify-content: center;
  align-items: center;
  top: calc(50% - 15px);
  bottom: calc(50% - 15px);
  ${({$direction}) => ($direction === 'left' ? 'left: 315px;' : 'right: 0;')}
  background: ${Colors.backgroundDefault()};
  z-index: 10;

  justify-content: center;
  align-items: center;
  cursor: pointer;
  display: flex;
  &:hover {
    background: ${Colors.backgroundDefaultHover()};
  }
`;

const PartitionRunMatrixContainer = styled.div`
  display: block;
`;

const Divider = styled.div`
  height: 1px;
  width: 100%;
  margin-top: 5px;
  border-top: 1px solid ${Colors.keylineDefault()};
`;

// add in the explorer fragment, so we can reconstruct the faux-plan steps from the exploded plan
// in the same way we construct the explorer graph
const PARTITION_STEP_STATUS_PIPELINE_QUERY = gql`
  query PartitionStepStatusPipelineQuery($pipelineSelector: PipelineSelector) {
    pipelineSnapshotOrError(activePipelineSelector: $pipelineSelector) {
      ... on PipelineSnapshot {
        id
        name
        solidHandles {
          ...PartitionMatrixSolidHandleFragment
        }
      }
    }
  }

  ${PARTITION_MATRIX_SOLID_HANDLE_FRAGMENT}
`;

const TOOLTIP_STYLE = JSON.stringify({
  top: 20,
  left: 10,
});

const PartitionSquare = ({
  step,
  runs,
  runsLoaded,
  hovered,
  setHovered,
  setFocused,
  partitionName,
}: {
  step?: MatrixStep;
  runs: PartitionMatrixStepRunFragment[];
  runsLoaded: boolean;
  hovered: PartitionRunSelection | null;
  minUnix: number;
  maxUnix: number;
  partitionName: string;
  setHovered: (hovered: PartitionRunSelection | null) => void;
  setFocused: (hovered: PartitionRunSelection | null) => void;
}) => {
  const [opened, setOpened] = React.useState(false);
  let squareStatus;

  if (!runsLoaded) {
    squareStatus = 'loading';
  } else if (step) {
    squareStatus = step.color.toLowerCase();
  } else if (runs.length === 0) {
    squareStatus = 'empty';
  } else {
    const runStatus = [...runs].reverse().find((r) => r.status !== RunStatus.CANCELED)?.status;
    if (runStatus) {
      squareStatus = runStatus.toLowerCase();
    } else {
      squareStatus = 'empty';
    }
  }
  const content = (
    <div
      className={`square ${squareStatus}`}
      onMouseEnter={() => setHovered({stepName: step?.name, partitionName})}
      onMouseLeave={() => setHovered(null)}
      data-tooltip={
        runsLoaded && !step ? (runs.length === 1 ? `1 run` : `${runs.length} runs`) : undefined
      }
      data-tooltip-style={TOOLTIP_STYLE}
    />
  );

  if (
    !opened &&
    (!runs.length || hovered?.stepName !== step?.name || hovered?.partitionName !== partitionName)
  ) {
    return content;
  }

  return (
    <Popover
      interactionKind="click"
      placement="bottom-start"
      onOpening={() => setOpened(true)}
      onClosed={() => setOpened(false)}
      content={
        <Menu>
          <MenuLink
            icon="open_in_new"
            text="Show logs from last run"
            to={linkToRunEvent(runs[runs.length - 1]!, {stepKey: step ? step.name : null})}
          />
          <MenuItem
            icon="settings_backup_restore"
            text={`View runs (${runs.length})`}
            onClick={() => setFocused({stepName: step?.name, partitionName})}
          />
        </Menu>
      }
    >
      {content}
    </Popover>
  );
};
