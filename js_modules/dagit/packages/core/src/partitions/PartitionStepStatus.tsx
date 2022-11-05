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
import * as React from 'react';
import styled from 'styled-components/macro';

import {useViewport} from '../gantt/useViewport';
import {linkToRunEvent} from '../runs/RunUtils';
import {RunFilterToken} from '../runs/RunsFilterInput';
import {MenuLink} from '../ui/MenuLink';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {PartitionRunList} from './PartitionRunList';
import {
  BOX_SIZE,
  GridColumn,
  GridFloatingContainer,
  LeftLabel,
  TopLabel,
  topLabelHeightForLabels,
  TopLabelTilted,
} from './RunMatrixUtils';
import {PartitionMatrixStepRunFragment} from './types/PartitionMatrixStepRunFragment';
import {
  PartitionStepStatusPipelineQuery,
  PartitionStepStatusPipelineQueryVariables,
} from './types/PartitionStepStatusPipelineQuery';
import {
  PARTITION_MATRIX_SOLID_HANDLE_FRAGMENT,
  MatrixStep,
  PartitionRuns,
  StatusSquareFinalColor,
  useMatrixData,
} from './useMatrixData';

interface PartitionRunSelection {
  partitionName: string;
  stepName?: string;
}

interface PartitionStepStatusProps {
  pipelineName: string;
  partitionNames: string[];
  partitions: PartitionRuns[];
  repoAddress: RepoAddress;
  runFilters?: RunFilterToken[];
  setRunFilters?: (val: RunFilterToken[]) => void;
  offset: number;
  setOffset: (val: number) => void;
  setPageSize: (val: number) => void;
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

export const PartitionStepStatus: React.FC<PartitionStepStatusProps> = (props) => {
  const {viewport, containerProps} = useViewport();
  const [hovered, setHovered] = React.useState<PartitionRunSelection | null>(null);
  const [focused, setFocused] = React.useState<PartitionRunSelection | null>(null);
  const {setPageSize} = props;

  React.useEffect(() => {
    if (viewport.width) {
      const pageSize = Math.ceil(viewport.width / BOX_SIZE) - BUFFER;
      setPageSize(pageSize);
    }
  }, [viewport.width, setPageSize]);

  // Retrieve the pipeline's structure
  const repositorySelector = repoAddressToSelector(props.repoAddress);
  const pipelineSelector = {...repositorySelector, pipelineName: props.pipelineName};
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
    partitionNames: props.partitionNames,
    partitions: props.partitions,
    stepQuery: '',
    solidHandles,
  });

  if (!data || !solidHandles) {
    return <span />;
  }

  const {stepRows, partitionColumns} = data;

  const sortPartitionSteps = (steps: MatrixStep[]) => {
    const stepsByName = {};
    steps.forEach((step) => (stepsByName[step.name] = step));
    return stepRows.map((stepRow) => stepsByName[stepRow.name]);
  };

  const BUFFER = 3;
  const visibleCount = Math.ceil(viewport.width / BOX_SIZE) - BUFFER;
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
            <LeftLabel style={{paddingLeft: 24}}>Last run</LeftLabel>
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

const PartitionSquare: React.FC<{
  step?: MatrixStep;
  runs: PartitionMatrixStepRunFragment[];
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
  } else if (runs.length === 0) {
    squareStatus = 'empty';
  } else if (step) {
    squareStatus = (StatusSquareFinalColor[step.color] || step.color).toLowerCase();
  } else {
    squareStatus = runs[runs.length - 1].status.toLowerCase();
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
