import {Colors, Position} from '@blueprintjs/core';
import {Tooltip2 as Tooltip} from '@blueprintjs/popover2';
import * as React from 'react';
import styled from 'styled-components/macro';

import {formatElapsedTime} from '../app/Util';
import {SidebarSection} from '../pipelines/SidebarComponents';
import {IRunMetadataDict, IStepState} from '../runs/RunMetadataProvider';
import {StepSelection} from '../runs/StepSelection';
import {Spinner} from '../ui/Spinner';

import {GanttChartMode} from './Constants';
import {boxStyleFor} from './GanttChartLayout';
import {RunGroupPanel} from './RunGroupPanel';

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
  const {preparing, executing, errored} = React.useMemo(() => {
    const keys = Object.keys(metadata.steps);
    const preparing = [];
    const executing = [];
    const errored = [];
    for (const key of keys) {
      const state = metadata.steps[key].state;
      switch (state) {
        case IStepState.PREPARING:
          preparing.push(key);
          break;
        case IStepState.RUNNING:
        case IStepState.UNKNOWN:
          executing.push(key);
          break;
        case IStepState.FAILED:
          errored.push(key);
      }
    }
    return {preparing, executing, errored};
  }, [metadata]);

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
    <div style={{overflowY: 'auto'}}>
      <RunGroupPanel runId={runId} />
      <SidebarSection title={isFinished ? 'Not Executed' : 'Preparing'}>
        <div>
          {preparing.length === 0 ? (
            <EmptyNotice>No steps are waiting to execute</EmptyNotice>
          ) : (
            preparing.map(renderStepItem)
          )}
        </div>
      </SidebarSection>
      <SidebarSection title="Executing">
        <div>
          {executing.length === 0 ? (
            <EmptyNotice>No steps are executing</EmptyNotice>
          ) : (
            executing.map(renderStepItem)
          )}
        </div>
      </SidebarSection>
      <SidebarSection title="Errored">
        <div>
          {errored.length === 0 ? (
            <EmptyNotice>No steps have errored</EmptyNotice>
          ) : (
            errored.map(renderStepItem)
          )}
        </div>
      </SidebarSection>
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
  font-size: 12px;
  padding: 12px;
`;
