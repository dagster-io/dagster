import * as React from "react";
import styled from "styled-components";
import { format as formatDate } from "date-fns";
import { Colors, Button, ButtonGroup, Dialog } from "@blueprintjs/core";
import { PipelineRunFragment } from "./types/PipelineRunFragment";

import ConfigEditor from "../configeditor/ConfigEditor";
import PipelineGraph from "../graph/PipelineGraph";
import { getDagrePipelineLayout } from "../graph/getFullSolidLayout";

type Props = {
  run: PipelineRunFragment;
};

enum ModalState {
  SolidSubset,
  Config,
  Closed
}

let getShortId = (run: { runId: string }) => run.runId.split("_");

const RunMetadataBar: React.FC<Props> = ({ run }) => {
  const [modalState, setModalState] = React.useState(ModalState.Closed);

  return (
    <>
      <BarContainer>
        <RunInfo>
          <RunName>Run {getShortId(run)}</RunName>
          <RunTime>{formatDate(run.startedAt, "MM/DD/YY hh:mm:ss A")}</RunTime>
        </RunInfo>
        <ButtonGroup>
          <Button small={true} onClick={() => setModalState(ModalState.Config)}>
            View Config
          </Button>
          {run.solidSubset && (
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
          configCode={run.config}
          readOnly={true}
          checkConfig={async () => ({ isValid: true })}
        />
      </Dialog>

      {run.solidSubset && (
        <Dialog
          icon="info-sign"
          onClose={() => setModalState(ModalState.Closed)}
          style={{ width: "80vw", maxWidth: 1400, height: "80vh" }}
          title={"Solids executed in this run"}
          usePortal={true}
          isOpen={modalState === ModalState.SolidSubset}
        >
          <PipelineGraph
            pipeline={run.pipeline}
            layout={getDagrePipelineLayout(run.pipeline)}
            highlightedSolids={run.pipeline.solids.filter(
              solid => run.solidSubset && run.solidSubset.includes(solid.name)
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
