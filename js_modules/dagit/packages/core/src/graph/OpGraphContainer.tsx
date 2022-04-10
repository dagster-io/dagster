import * as React from 'react';

import {OpNameOrPath} from '../ops/OpNameOrPath';
import {LoadingNotice} from '../pipelines/GraphNotices';
import {GraphExplorerSolidHandleFragment} from '../pipelines/types/GraphExplorerSolidHandleFragment';

import {OpGraph} from './OpGraph';
import {useOpLayout} from './asyncGraphLayout';
import {OpGraphOpFragment} from './types/OpGraphOpFragment';

interface Props {
  pipelineName: string;
  ops: OpGraphOpFragment[];
  focusOps: OpGraphOpFragment[];
  highlightedOps: OpGraphOpFragment[];
  selectedHandle?: GraphExplorerSolidHandleFragment;
  parentHandle?: GraphExplorerSolidHandleFragment;
  onClickOp?: (arg: OpNameOrPath) => void;
  onEnterSubgraph?: (arg: OpNameOrPath) => void;
  onLeaveSubgraph?: () => void;
  onClickBackground?: () => void;
}

export const OpGraphContainer: React.FC<Props> = (props) => {
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
    <OpGraph
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
