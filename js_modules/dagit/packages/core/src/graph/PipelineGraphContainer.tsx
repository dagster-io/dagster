import * as React from 'react';

import {OpNameOrPath} from '../ops/OpNameOrPath';
import {LoadingNotice} from '../pipelines/GraphNotices';
import {GraphExplorerSolidHandleFragment} from '../pipelines/types/GraphExplorerSolidHandleFragment';

import {PipelineGraph} from './PipelineGraph';
import {useOpLayout} from './asyncGraphLayout';
import {PipelineGraphOpFragment} from './types/PipelineGraphOpFragment';

interface Props {
  pipelineName: string;
  ops: PipelineGraphOpFragment[];
  focusOps: PipelineGraphOpFragment[];
  highlightedOps: PipelineGraphOpFragment[];
  selectedHandle?: GraphExplorerSolidHandleFragment;
  parentHandle?: GraphExplorerSolidHandleFragment;
  onClickOp?: (arg: OpNameOrPath) => void;
  onEnterSubgraph?: (arg: OpNameOrPath) => void;
  onLeaveSubgraph?: () => void;
  onClickBackground?: () => void;
}

export const PipelineGraphContainer: React.FC<Props> = (props) => {
  const {
    pipelineName,
    ops,
    focusOps,
    highlightedOps,
    selectedHandle,
    parentHandle,
    onClickOp,
    onEnterSubgraph,
    onLeaveSubgraph,
    onClickBackground,
  } = props;
  const parentOp = parentHandle && parentHandle.solid;
  const {layout, loading, async} = useOpLayout(ops, parentOp);

  if (loading || !layout) {
    return <LoadingNotice async={async} nodeType="op" />;
  }

  return (
    <PipelineGraph
      pipelineName={pipelineName}
      ops={ops}
      focusOps={focusOps}
      highlightedOps={highlightedOps}
      selectedHandleID={selectedHandle && selectedHandle.handleID}
      selectedOp={selectedHandle && selectedHandle.solid}
      parentHandleID={parentHandle && parentHandle.handleID}
      parentOp={parentOp}
      onClickOp={onClickOp}
      onClickBackground={onClickBackground}
      onEnterSubgraph={onEnterSubgraph}
      onLeaveSubgraph={onLeaveSubgraph}
      layout={layout}
    />
  );
};
