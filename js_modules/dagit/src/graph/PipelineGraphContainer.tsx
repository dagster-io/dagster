import * as React from "react";
import PipelineGraph from "./PipelineGraph";
import { SolidNameOrPath } from "../PipelineExplorer";
import { PipelineGraphSolidFragment } from "./types/PipelineGraphSolidFragment";
import { PipelineExplorerSolidHandleFragment } from "../types/PipelineExplorerSolidHandleFragment";
import { PipelineExplorerParentSolidHandleFragment } from "../types/PipelineExplorerParentSolidHandleFragment";
import { getDagrePipelineLayout } from "./getFullSolidLayout";

interface IPipelineGraphContainerProps {
  pipelineName: string;
  backgroundColor: string;
  solids: PipelineGraphSolidFragment[];
  focusSolids: PipelineGraphSolidFragment[];
  highlightedSolids: PipelineGraphSolidFragment[];
  selectedHandle?: PipelineExplorerSolidHandleFragment;
  parentHandle?: PipelineExplorerParentSolidHandleFragment;
  onClickSolid?: (arg: SolidNameOrPath) => void;
  onEnterCompositeSolid?: (arg: SolidNameOrPath) => void;
  onLeaveCompositeSolid?: () => void;
  onClickBackground?: () => void;
}

export const PipelineGraphContainer = (props: IPipelineGraphContainerProps) => {
  const {
    pipelineName,
    backgroundColor,
    solids,
    focusSolids,
    highlightedSolids,
    selectedHandle,
    parentHandle,
    onClickSolid,
    onEnterCompositeSolid,
    onLeaveCompositeSolid,
    onClickBackground
  } = props;

  const parentSolid = parentHandle && parentHandle.solid;
  const layout = React.useMemo(
    () => getDagrePipelineLayout(solids, parentSolid),
    [solids, parentSolid]
  );

  return (
    <PipelineGraph
      pipelineName={pipelineName}
      backgroundColor={backgroundColor}
      solids={solids}
      focusSolids={focusSolids}
      highlightedSolids={highlightedSolids}
      selectedHandleID={selectedHandle && selectedHandle.handleID}
      selectedSolid={selectedHandle && selectedHandle.solid}
      parentHandleID={parentHandle && parentHandle.handleID}
      parentSolid={parentSolid}
      onClickSolid={onClickSolid}
      onClickBackground={onClickBackground}
      onEnterCompositeSolid={onEnterCompositeSolid}
      onLeaveCompositeSolid={onLeaveCompositeSolid}
      layout={layout}
    />
  );
};
