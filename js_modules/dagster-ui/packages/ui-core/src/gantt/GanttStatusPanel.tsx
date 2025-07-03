import {Spinner, Tooltip} from '@dagster-io/ui-components';
import clsx from 'clsx';
import * as React from 'react';

import {GanttChartMode} from './Constants';
import {isPlannedDynamicStep} from './DynamicStepSupport';
import {boxStyleFor} from './GanttChartLayout';
import {RunGroupPanel} from './RunGroupPanel';
import styles from './css/GanttStatusPanel.module.css';
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
              <div className={styles.emptyNotice}>No steps are waiting to execute</div>
            ) : (
              preparing.map(renderStepItem)
            )}
          </div>
        </SidebarSection>
        <SidebarSection title={`Executing (${executing.length})`}>
          <div>
            {executing.length === 0 ? (
              <div className={styles.emptyNotice}>No steps are executing</div>
            ) : (
              executing.map(renderStepItem)
            )}
          </div>
        </SidebarSection>
        <SidebarSection title={`Errored (${errored.length})`}>
          <div>
            {errored.length === 0 ? (
              <div className={styles.emptyNotice}>No steps have errored</div>
            ) : (
              errored.map(renderStepItem)
            )}
          </div>
        </SidebarSection>
        <SidebarSection collapsedByDefault title={`Succeeded (${succeeded.length})`}>
          <div>
            {succeeded.length === 0 ? (
              <div className={styles.emptyNotice}>No steps have succeeded</div>
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
    <div
      key={name}
      className={clsx(styles.stepItemContainer, selected && styles.selected)}
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
      <div className={styles.stepLabel}>{name}</div>
      {step?.start && (
        <div className={styles.elapsed}>{formatElapsedTimeWithoutMsec(end - step.start)}</div>
      )}
    </div>
  );
};

export const StepStatusDot = ({
  children,
  ...rest
}: {
  children?: React.ReactNode;
} & React.HTMLProps<HTMLDivElement>) => (
  <div className={styles.stepStatusDot} {...rest}>
    {children}
  </div>
);
