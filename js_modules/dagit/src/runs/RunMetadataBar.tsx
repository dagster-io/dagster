import * as React from "react";
import {
  Colors,
  Button,
  ButtonGroup,
  Dialog,
} from "@blueprintjs/core";
import { RunMetadataBar } from "./types/RunMetadataBar";
import { PipelineRunFragment } from "./types/PipelineRunFragment";
import styled from "styled-components";
import { format as formatDate } from "date-fns";
import PipelineGraph from "../graph/PipelineGraph";
import { getDagrePipelineLayout } from "../graph/getFullSolidLayout";
import ConfigEditor from "../configeditor/ConfigEditor";

type Props = {
  run: PipelineRunFragment;
};

enum ModalState {
  SolidSubset,
  Config,
  Closed
}

const RunMetadataBar: React.FC<Props> = props => {
  const [modalState, setModalState] = React.useState(ModalState.Closed);

  return (
    <>
      <BarContainer>
        <RunInfo>
          <RunName>Run {props.run.runId.split("-")[0]}</RunName>
          <RunTime>
            {formatDate(props.run.startedAt, "MM/DD/YY hh:mm:ss A")}
          </RunTime>
        </RunInfo>
        <ButtonGroup>
          <Button small={true} onClick={() => setModalState(ModalState.Config)}>
            View Config
          </Button>
          {props.run.solidSubset && (
            <Button
              small={true}
              onClick={() => setModalState(ModalState.SolidSubset)}
            >
              View Solid Subset
            </Button>
          )}
        </ButtonGroup>
      </BarContainer>

      <Dialog
        icon="info-sign"
        onClose={() => setModalState(ModalState.Closed)}
        style={{ width: "80vw", maxWidth: 1400, height: "80vh" }}
        title={"Config for this run"}
        usePortal={true}
        isOpen={modalState === ModalState.Config}
      >
        <ConfigEditor
          onConfigChange={() => {}}
          configCode={props.run.config}
          readOnly={true}
          checkConfig={async () => {
            return { isValid: true };
          }}
        />
      </Dialog>

      {props.run.solidSubset && (
        <Dialog
          icon="info-sign"
          onClose={() => setModalState(ModalState.Closed)}
          style={{ width: "80vw", maxWidth: 1400, height: "80vh" }}
          title={"Solids executed in this run"}
          usePortal={true}
          isOpen={modalState === ModalState.SolidSubset}
        >
          <PipelineGraph
            pipeline={props.run.pipeline}
            layout={getDagrePipelineLayout(props.run.pipeline)}
            highlightedSolids={props.run.pipeline.solids.filter(
              solid =>
                props.run.solidSubset &&
                props.run.solidSubset.includes(solid.name)
            )}
          />
        </Dialog>
      )}
    </>
  );
};

export default RunMetadataBar;

const BarContainer = styled.div`
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  background: ${Colors.WHITE};
  height: 40px;
  align-items: center;
  padding: 5px 15px;
  border-bottom: 1px solid ${Colors.GRAY4};
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.07);
`;

const RunInfo = styled.div`
  display: flex;
  justify-content: flex-start;
`;

const RunName = styled.div`
  font-weight: 700;
  margin-right: 10px;
`;

const RunTime = styled.div`
  color: ${Colors.GRAY4};
`;
