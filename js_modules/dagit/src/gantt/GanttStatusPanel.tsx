import {Colors, Tooltip, Position} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components/macro';

import {formatElapsedTime} from 'src/app/Util';
import {GanttChartMode} from 'src/gantt/Constants';
import {boxStyleFor} from 'src/gantt/GanttChartLayout';
import {RunGroupPanel} from 'src/gantt/RunGroupPanel';
import {IRunMetadataDict, IStepState} from 'src/runs/RunMetadataProvider';
import {StepSelection} from 'src/runs/StepSelection';
import {Spinner} from 'src/ui/Spinner';

interface GanttStatusPanelProps {
  metadata: IRunMetadataDict;
  selection: StepSelection;
  runId: string;
  nowMs: number;

  onClickStep?: (step: string, evt: React.MouseEvent<any>) => void;
  onHighlightStep?: (step: string | null) => void;
  onDoubleClickStep?: (step: string) => void;
}

export const GanttStatusPanel: React.FunctionComponent<GanttStatusPanelProps> = ({
  runId,
  nowMs,
  metadata,
  selection,
  onClickStep,
  onDoubleClickStep,
  onHighlightStep,
}) => {
  const preparing = Object.keys(metadata.steps).filter(
    (key) => metadata.steps[key].state === IStepState.PREPARING,
  );
  const executing = Object.keys(metadata.steps).filter((key) =>
    [IStepState.RUNNING, IStepState.UNKNOWN].includes(metadata.steps[key].state),
  );
  const errored = Object.keys(metadata.steps).filter(
    (key) => metadata.steps[key].state === IStepState.FAILED,
  );
  const renderStepItem = (stepName: string) => (
    <StepItem
      nowMs={nowMs}
      name={stepName}
      key={stepName}
      metadata={metadata}
      selected={selection.keys.includes(stepName)}
      onClick={onClickStep}
      onDoubleClick={onDoubleClickStep}
      onHover={onHighlightStep}
    />
  );
  const isFinished = metadata?.exitedAt && metadata.exitedAt > 0;
  return (
    <div style={{display: 'flex', flexDirection: 'column', minHeight: 0, overflowY: 'auto'}}>
      <RunGroupPanel runId={runId} />
      <SectionHeader>{isFinished ? 'Not Executed' : 'Preparing'}</SectionHeader>
      <Section>{preparing.map(renderStepItem)}</Section>
      {preparing.length === 0 && <EmptyNotice>No steps are waiting to execute</EmptyNotice>}
      <SectionHeader>Executing</SectionHeader>
      <Section>{executing.map(renderStepItem)}</Section>
      {executing.length === 0 && <EmptyNotice>No steps are executing</EmptyNotice>}
      <SectionHeader>Errored</SectionHeader>
      <Section>{errored.map(renderStepItem)}</Section>
    </div>
  );
};

const StepItem: React.FunctionComponent<{
  name: string;
  selected: boolean;
  metadata: IRunMetadataDict;
  nowMs: number;
  onClick?: (step: string, evt: React.MouseEvent<any>) => void;
  onHover?: (name: string | null) => void;
  onDoubleClick?: (name: string) => void;
}> = ({nowMs, name, selected, metadata, onClick, onHover, onDoubleClick}) => {
  const step = metadata.steps[name];
  const end = step.end ?? nowMs;
  return (
    <StepItemContainer
      key={name}
      selected={selected}
      onClick={(evt: React.MouseEvent<any>) => onClick?.(name, evt)}
      onDoubleClick={() => onDoubleClick?.(name)}
      onMouseEnter={() => onHover?.(name)}
      onMouseLeave={() => onHover?.(null)}
    >
      {step.state === IStepState.RUNNING ? (
        <Spinner purpose="body-text" />
      ) : step.state === IStepState.UNKNOWN ? (
        <Tooltip
          // Modifiers are to prevent flickering: https://github.com/palantir/blueprint/issues/4019
          modifiers={{
            preventOverflow: {enabled: false},
            flip: {enabled: false},
          }}
          position={Position.BOTTOM}
          content={
            'Unknown step state. Pipeline execution completed without step execution completion.'
          }
        >
          {'?'}
        </Tooltip>
      ) : (
        <StepStatusDot
          style={{
            ...boxStyleFor(metadata.steps[name]?.state, {
              metadata,
              options: {mode: GanttChartMode.WATERFALL_TIMED},
            }),
          }}
        />
      )}
      <StepLabel>{name}</StepLabel>
      {step.start && <Elapsed>{formatElapsedTime(end - step.start)}</Elapsed>}
    </StepItemContainer>
  );
};

const SectionHeader = styled.div`
  font-size: 11px;
  padding: 3px 6px;
  text-transform: uppercase;
  background: ${Colors.LIGHT_GRAY4};
  border-bottom: 1px solid ${Colors.LIGHT_GRAY1};
  color: ${Colors.GRAY3};
  height: 20px;
`;

const Section = styled.div`
  overflow-y: auto;
`;

const StepLabel = styled.div`
  margin-left: 5px;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
`;

const StepItemContainer = styled.div<{selected: boolean}>`
  display: flex;
  line-height: 28px;
  height: 28px;
  padding: 0 5px;
  align-items: center;
  border-bottom: 1px solid ${Colors.LIGHT_GRAY1};
  font-size: 13px;
  ${({selected}) => selected && `background: ${Colors.LIGHT_GRAY4};`}

  &:hover {
    background: ${Colors.LIGHT_GRAY3};
  }
`;

const StepStatusDot = styled.div`
  width: 11px;
  height: 11px;
  flex-shrink: 0;
  border-radius: 5.5px;
`;

const Elapsed = styled.div`
  color: ${Colors.GRAY3};
  font-variant-numeric: tabular-nums;
`;

const EmptyNotice = styled.div`
  padding: 7px 24px;
  font-size: 13px;
`;
