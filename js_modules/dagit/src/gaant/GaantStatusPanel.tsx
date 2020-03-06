import * as React from "react";
import styled from "styled-components/macro";
import { GaantChartExecutionPlanFragment } from "./types/GaantChartExecutionPlanFragment";
import { IRunMetadataDict, IStepState } from "../RunMetadataProvider";
import { RunFragment } from "../runs/types/RunFragment";
import { Spinner, Colors } from "@blueprintjs/core";
import { GaantChartMode } from "./Constants";
import { boxStyleFor } from "./GaantChartLayout";
import { formatElapsedTime } from "../Util";

interface GaantStatusPanelProps {
  plan: GaantChartExecutionPlanFragment;
  metadata: IRunMetadataDict;
  selectedStep: string | null;
  run?: RunFragment;
  nowMs: number;

  onApplyStepFilter?: (step: string) => void;
  onHighlightStep?: (step: string | null) => void;
  onDoubleClickStep?: (step: string) => void;
}

export const GaantStatusPanel: React.FunctionComponent<GaantStatusPanelProps> = ({
  nowMs,
  metadata,
  selectedStep,
  onApplyStepFilter,
  onDoubleClickStep,
  onHighlightStep
}) => {
  const executing = Object.keys(metadata.steps).filter(
    key => metadata.steps[key].state === IStepState.RUNNING
  );
  const errored = Object.keys(metadata.steps).filter(
    key => metadata.steps[key].state === IStepState.FAILED
  );
  const renderStepItem = (stepName: string) => (
    <StepItem
      nowMs={nowMs}
      name={stepName}
      key={stepName}
      metadata={metadata}
      selected={selectedStep === stepName}
      onClick={onApplyStepFilter}
      onDoubleClick={onDoubleClickStep}
      onHover={onHighlightStep}
    />
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", minHeight: 0 }}>
      <SectionHeader>Executing</SectionHeader>
      <Section>{executing.map(renderStepItem)}</Section>
      {executing.length === 0 && (
        <EmptyNotice>No steps are executing</EmptyNotice>
      )}
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
  onClick?: (name: string) => void;
  onHover?: (name: string | null) => void;
  onDoubleClick?: (name: string) => void;
}> = ({ nowMs, name, selected, metadata, onClick, onHover, onDoubleClick }) => {
  const step = metadata.steps[name];
  const end = step.end ?? nowMs;
  return (
    <StepItemContainer
      key={name}
      selected={selected}
      onClick={() => onClick?.(name)}
      onDoubleClick={() => onDoubleClick?.(name)}
      onMouseEnter={() => onHover?.(name)}
      onMouseLeave={() => onHover?.(null)}
    >
      {step.state === IStepState.RUNNING ? (
        <Spinner size={15} />
      ) : (
        <StepStatusDot
          style={{
            ...boxStyleFor(name, {
              metadata,
              options: { mode: GaantChartMode.WATERFALL_TIMED }
            })
          }}
        />
      )}
      <StepLabel>{name}</StepLabel>
      <Elapsed>{formatElapsedTime(end - step.start!)}</Elapsed>
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

const StepItemContainer = styled.div<{ selected: boolean }>`
  display: flex;
  line-height: 28px;
  height: 28px;
  padding: 0 5px;
  align-items: center;
  border-bottom: 1px solid ${Colors.LIGHT_GRAY1};
  font-size: 13px;
  ${({ selected }) => selected && `background: ${Colors.LIGHT_GRAY4};`}

  &:hover {
    background: ${Colors.LIGHT_GRAY3};
  }
`;

const StepStatusDot = styled.div`
  width: 15px;
  height: 15px;
  flex-shrink: 0;
  border-radius: 7.5px;
`;

const Elapsed = styled.div`
  color: ${Colors.GRAY3};
`;

const EmptyNotice = styled.div`
  padding: 7px 24px;
  font-size: 13px;
`;
