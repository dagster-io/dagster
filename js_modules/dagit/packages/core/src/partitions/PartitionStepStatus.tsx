import {gql, useQuery} from '@apollo/client';
import {
  Box,
  Button,
  Colors,
  DialogFooter,
  Dialog,
  Icon,
  MenuItem,
  Menu,
  Popover,
} from '@dagster-io/ui';
import keyBy from 'lodash/keyBy';
import * as React from 'react';
import styled from 'styled-components/macro';

import {GraphQueryItem} from '../app/GraphQueryImpl';
import {tokenForAssetKey} from '../asset-graph/Utils';
import {PartitionHealthData, PartitionHealthDimension} from '../assets/usePartitionHealthData';
import {GanttChartMode} from '../gantt/Constants';
import {buildLayout} from '../gantt/GanttChartLayout';
import {useViewport} from '../gantt/useViewport';
import {graphql} from '../graphql';
import {PartitionMatrixStepRunFragmentFragment, RunStatus} from '../graphql/graphql';
import {linkToRunEvent} from '../runs/RunUtils';
import {RunFilterToken} from '../runs/RunsFilterInput';
import {MenuLink} from '../ui/MenuLink';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {PartitionRunList} from './PartitionRunList';
import {PartitionState} from './PartitionStatus';
import {
  BOX_SIZE,
  GridColumn,
  GridFloatingContainer,
  LeftLabel,
  TopLabel,
  topLabelHeightForLabels,
  TopLabelTilted,
} from './RunMatrixUtils';
import {MatrixStep, PartitionRuns, useMatrixData, MatrixData} from './useMatrixData';

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

export const PartitionPerAssetStatus: React.FC<
  Omit<PartitionStepStatusBaseProps, 'partitionNames'> & {
    assetHealth: PartitionHealthData[];
    assetQueryItems: GraphQueryItem[];
    rangeDimensionIdx: number;
    rangeDimension: PartitionHealthDimension;
  }
> = ({assetHealth, rangeDimension, rangeDimensionIdx, assetQueryItems, ...rest}) => {
  const healthByAssetKey = keyBy(assetHealth, (a) => tokenForAssetKey(a.assetKey));

  const layout = buildLayout({nodes: assetQueryItems, mode: GanttChartMode.FLAT});
  const layoutBoxesWithRangeDimension = layout.boxes.filter(
    (b) =>
      healthByAssetKey[b.node.name]?.dimensions[rangeDimensionIdx]?.name === rangeDimension.name,
  );

  const data: MatrixData = {
    stepRows: layoutBoxesWithRangeDimension.map((box) => ({
      x: box.x,
      name: box.node.name,
      totalFailurePercent: 0,
      finalFailurePercent: 0,
    })),
    partitions: [],
    partitionColumns: rangeDimension.partitionKeys.map((partitionKey, idx) => ({
      idx,
      name: partitionKey,
      runsLoaded: true,
      runs: [],
      steps: layoutBoxesWithRangeDimension.map((box) => ({
        name: box.node.name,
        unix: 0,
        color: partitionStateToStatusSquareColor(
          healthByAssetKey[box.node.name].stateForSingleDimension(rangeDimensionIdx, partitionKey),
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

export const partitionStateToStatusSquareColor = (state: PartitionState) => {
  return state === PartitionState.SUCCESS
    ? 'SUCCESS'
    : state === PartitionState.SUCCESS_MISSING
    ? 'SUCCESS-MISSING'
    : 'MISSING';
};

export const PartitionPerOpStatus: React.FC<
  PartitionStepStatusBaseProps & {
    repoAddress: RepoAddress;
    partitions: PartitionRuns[];
  }
> = ({repoAddress, pipelineName, partitions, partitionNames, ...rest}) => {
  // Retrieve the pipeline's structure
  const repositorySelector = repoAddressToSelector(repoAddress);
  const pipelineSelector = {...repositorySelector, pipelineName};
  const pipeline = useQuery(PARTITION_STEP_STATUS_PIPELINE_QUERY, {
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

const PartitionStepStatus: React.FC<
  PartitionStepStatusBaseProps & {
    data: MatrixData;
    showLatestRun: boolean;
  }
> = (props) => {
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
    steps.forEach((step) => (stepsByName[step.name] = step));
    return stepRows.map((stepRow) => stepsByName[stepRow.name]);
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
  border: 1px solid ${Colors.KeylineGray};
  border-radius: 3px;
  display: flex;
  justify-content: center;
  align-items: center;
  top: calc(50% - 15px);
  bottom: calc(50% - 15px);
  ${({$direction}) => ($direction === 'left' ? 'left: 315px;' : 'right: 0;')}
  background: white;
  z-index: 10;

  justify-content: center;
  align-items: center;
  cursor: pointer;
  display: flex;
  &:hover {
    background: #ececec;
  }
`;

const PartitionRunMatrixContainer = styled.div`
  display: block;
`;

const Divider = styled.div`
  height: 1px;
  width: 100%;
  margin-top: 5px;
  border-top: 1px solid ${Colors.KeylineGray};
`;

export const PARTITION_STEP_STATUS_RUN_FRAGMENT = gql`
  fragment PartitionStepStatusRun on Run {
    id
    runId
    tags {
      key
      value
    }
    stepStats {
      __typename
      stepKey
      status
    }
  }
`;

// add in the explorer fragment, so we can reconstruct the faux-plan steps from the exploded plan
// in the same way we construct the explorer graph
const PARTITION_STEP_STATUS_PIPELINE_QUERY = graphql(`
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
`);

const TOOLTIP_STYLE = JSON.stringify({
  top: 20,
  left: 10,
});

const PartitionSquare: React.FC<{
  step?: MatrixStep;
  runs: PartitionMatrixStepRunFragmentFragment[];
  runsLoaded: boolean;
  hovered: PartitionRunSelection | null;
  minUnix: number;
  maxUnix: number;
  partitionName: string;
  setHovered: (hovered: PartitionRunSelection | null) => void;
  setFocused: (hovered: PartitionRunSelection | null) => void;
}> = ({step, runs, runsLoaded, hovered, setHovered, setFocused, partitionName}) => {
  const [opened, setOpened] = React.useState(false);
  let squareStatus;

  if (!runsLoaded) {
    squareStatus = 'loading';
  } else if (step) {
    squareStatus = step.color.toLowerCase();
  } else if (runs.length === 0) {
    squareStatus = 'empty';
  } else {
    const runStatus = runs[runs.length - 1].status;
    squareStatus = runStatus === RunStatus.CANCELED ? 'failure' : runStatus.toLowerCase();
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
            to={linkToRunEvent(runs[runs.length - 1], {stepKey: step ? step.name : null})}
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
