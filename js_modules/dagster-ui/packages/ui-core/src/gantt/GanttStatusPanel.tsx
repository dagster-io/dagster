import {Colors, Spinner, Tooltip} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

import {GanttChartMode} from './Constants';
import {isPlannedDynamicStep} from './DynamicStepSupport';
import {boxStyleFor} from './GanttChartLayout';
import {RunGroupPanel} from './RunGroupPanel';
import {GraphQueryItem} from '../app/GraphQueryImpl';
import {formatElapsedTimeWithoutMsec} from '../app/Util';
import {SidebarSection} from '../pipelines/SidebarComponents';
import {IRunMetadataDict, IStepState} from '../runs/RunMetadataProvider';
import {StepSelection} from '../runs/StepSelection';

interface GanttStatusPanelProps {
  graph: GraphQueryItem[];
  metadata: IRunMetadataDict;
  selection: StepSelection;
  runId: string;
  nowMs: number;

  onClickStep?: (step: string, evt: React.MouseEvent<any>) => void;
  onHighlightStep?: (step: string | null) => void;
  onDoubleClickStep?: (step: string) => void;
}

export const GanttStatusPanel = React.memo(
  ({
    runId,
    nowMs,
    graph,
    metadata,
    selection,
    onClickStep,
    onDoubleClickStep,
    onHighlightStep,
  }: GanttStatusPanelProps) => {
    const selectedKeysSet = React.useMemo(() => new Set(selection.keys), [selection.keys]);
    const {preparing, executing, errored, succeeded, notExecuted} = React.useMemo(() => {
      const keys = Object.keys(metadata.steps);
      const preparing = [];
      const executing = [];
      const errored = [];
      const succeeded = [];
      const notExecuted = [];
      for (const key of keys) {
        const state = metadata.steps[key]!.state;
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
            break;
          case IStepState.SUCCEEDED:
            succeeded.push(key);
            break;
        }
      }

      for (const node of graph) {
        const name = node.name;
        // Leave out [?] steps since they don't receive event log entries or have states
        if (!isPlannedDynamicStep(name) && !metadata.steps[name]?.state) {
          notExecuted.push(name);
        }
      }
      return {preparing, executing, errored, succeeded, notExecuted};
    }, [metadata, graph]);

    const renderStepItem = (stepName: string) => (
      <StepItem
        nowMs={nowMs}
        name={stepName}
        key={stepName}
        metadata={metadata}
        selected={selectedKeysSet.has(stepName)}
        onClick={onClickStep}
        onDoubleClick={onDoubleClickStep}
        onHover={onHighlightStep}
      />
    );

    return (
      <div style={{overflowY: 'auto'}}>
        <RunGroupPanel
          runId={runId}
          runStatusLastChangedAt={
            metadata.exitedAt || metadata.startedProcessAt || metadata.startedPipelineAt || 0
          }
        />
        <SidebarSection title={`Preparing (${preparing.length})`}>
          <div>
            {preparing.length === 0 ? (
              <EmptyNotice>No steps are waiting to execute</EmptyNotice>
            ) : (
              preparing.map(renderStepItem)
            )}
          </div>
        </SidebarSection>
        <SidebarSection title={`Executing (${executing.length})`}>
          <div>
            {executing.length === 0 ? (
              <EmptyNotice>No steps are executing</EmptyNotice>
            ) : (
              executing.map(renderStepItem)
            )}
          </div>
        </SidebarSection>
        <SidebarSection title={`Errored (${errored.length})`}>
          <div>
            {errored.length === 0 ? (
              <EmptyNotice>No steps have errored</EmptyNotice>
            ) : (
              errored.map(renderStepItem)
            )}
          </div>
        </SidebarSection>
        <SidebarSection collapsedByDefault title={`Succeeded (${succeeded.length})`}>
          <div>
            {succeeded.length === 0 ? (
              <EmptyNotice>No steps have succeeded</EmptyNotice>
            ) : (
              succeeded.map(renderStepItem)
            )}
          </div>
        </SidebarSection>
        {notExecuted.length > 0 ? (
          <SidebarSection collapsedByDefault title={`Not executed (${notExecuted.length})`}>
            <div>{notExecuted.map(renderStepItem)}</div>
          </SidebarSection>
        ) : null}
      </div>
    );
  },
);

const StepItem = ({
  nowMs,
  name,
  selected,
  metadata,
  onClick,
  onHover,
  onDoubleClick,
}: {
  name: string;
  selected: boolean;
  metadata: IRunMetadataDict;
  nowMs: number;
  onClick?: (step: string, evt: React.MouseEvent<any>) => void;
  onHover?: (name: string | null) => void;
  onDoubleClick?: (name: string) => void;
}) => {
  const step = metadata.steps[name];
  const end = (step && step.end) ?? nowMs;
  return (
    <StepItemContainer
      key={name}
      selected={selected}
      onClick={(evt: React.MouseEvent<any>) => onClick?.(name, evt)}
      onDoubleClick={() => onDoubleClick?.(name)}
      onMouseEnter={() => onHover?.(name)}
      onMouseLeave={() => onHover?.(null)}
    >
      {step?.state === IStepState.RUNNING ? (
        <Spinner purpose="body-text" />
      ) : step?.state === IStepState.UNKNOWN ? (
        <Tooltip
          // Modifiers are to prevent flickering: https://github.com/palantir/blueprint/issues/4019
          modifiers={{
            preventOverflow: {enabled: false},
            flip: {enabled: false},
          }}
          position="bottom"
          content="Unknown step state. Run completed without step execution completion."
        >
          <StepStatusDot>?</StepStatusDot>
        </Tooltip>
      ) : (
        <StepStatusDot
          style={{
            ...boxStyleFor(step?.state, {
              metadata,
              options: {mode: GanttChartMode.WATERFALL_TIMED},
            }),
          }}
        />
      )}
      <StepLabel>{name}</StepLabel>
      {step?.start && <Elapsed>{formatElapsedTimeWithoutMsec(end - step.start)}</Elapsed>}
    </StepItemContainer>
  );
};

const StepLabel = styled.div`
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
`;

const StepItemContainer = styled.div<{selected: boolean}>`
  display: flex;
  line-height: 32px;
  height: 32px;
  padding: 0 14px 0 6px;
  gap: 6px;
  align-items: center;
  border-bottom: 1px solid ${Colors.keylineDefault()};
  font-size: 12px;
  ${({selected}) => selected && `background: ${Colors.backgroundLight()};`}

  &:hover {
    background: ${Colors.backgroundLightHover()};
  }
`;

export const StepStatusDot = styled.div`
  width: 12px;
  height: 12px;
  flex-shrink: 0;
  border-radius: 50%;
  text-align: center;
  line-height: 12px;
`;

const Elapsed = styled.div`
  color: ${Colors.textLight()};
  font-variant-numeric: tabular-nums;
`;

const EmptyNotice = styled.div`
  min-height: 32px;
  font-size: 12px;
  padding: 8px 24px;
  color: ${Colors.textLight()};
`;
