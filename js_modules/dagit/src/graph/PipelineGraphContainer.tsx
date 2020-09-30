import {ProgressBar} from '@blueprintjs/core';
import * as React from 'react';

import {SolidNameOrPath} from 'src/PipelineExplorer';
import PipelineGraph from 'src/graph/PipelineGraph';
import {asyncDagrePipelineLayout, getDagrePipelineLayout} from 'src/graph/getFullSolidLayout';
import {IFullPipelineLayout} from 'src/graph/layout';
import {PipelineGraphSolidFragment} from 'src/graph/types/PipelineGraphSolidFragment';
import {PipelineExplorerSolidHandleFragment} from 'src/types/PipelineExplorerSolidHandleFragment';

const ASYNC_LAYOUT_SOLID_COUNT = 50;

interface IPipelineGraphContainerProps {
  pipelineName: string;
  backgroundColor: string;
  solids: PipelineGraphSolidFragment[];
  focusSolids: PipelineGraphSolidFragment[];
  highlightedSolids: PipelineGraphSolidFragment[];
  selectedHandle?: PipelineExplorerSolidHandleFragment;
  parentHandle?: PipelineExplorerSolidHandleFragment;
  onClickSolid?: (arg: SolidNameOrPath) => void;
  onEnterCompositeSolid?: (arg: SolidNameOrPath) => void;
  onLeaveCompositeSolid?: () => void;
  onClickBackground?: () => void;
}

export function PipelineGraphContainer(props: IPipelineGraphContainerProps) {
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
    onClickBackground,
  } = props;
  const parentSolid = parentHandle && parentHandle.solid;
  const [loading, setLoading] = React.useState(false);
  const [layoutSolidKey, setLayoutSolidKey] = React.useState('');
  const [layout, setLayout] = React.useState<IFullPipelineLayout | undefined>();
  const solidKey = solids.map((x) => x.name).join('|');
  const parentSolidKey = parentSolid && parentSolid.name;

  React.useEffect(() => {
    async function delegateDagrePipelineLayout() {
      setLoading(true);
      const _layout = (await asyncDagrePipelineLayout(solids, parentSolid)) as IFullPipelineLayout;
      setLayout(_layout);
      setLoading(false);
      setLayoutSolidKey(solidKey);
    }
    if (solids.length < ASYNC_LAYOUT_SOLID_COUNT) {
      setLayout(getDagrePipelineLayout(solids, parentSolid));
      setLayoutSolidKey(solidKey);
      setLoading(false);
    } else {
      delegateDagrePipelineLayout();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [solidKey, parentSolidKey]);

  if (loading || !layout || solidKey !== layoutSolidKey) {
    return <PipelineGraphLoading backgroundColor={backgroundColor} />;
  }

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
}

function PipelineGraphLoading({backgroundColor}: {backgroundColor: string}) {
  return (
    <div
      style={{
        backgroundColor,
        position: 'absolute',
        top: 0,
        bottom: 0,
        left: 0,
        right: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <div style={{maxWidth: 600, width: '75%'}}>
        <ProgressBar />
      </div>
    </div>
  );
}
