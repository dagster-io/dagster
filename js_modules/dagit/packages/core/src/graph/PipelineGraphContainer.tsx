import * as React from 'react';
import styled from 'styled-components/macro';

import {OpNameOrPath} from '../ops/OpNameOrPath';
import {GraphExplorerSolidHandleFragment} from '../pipelines/types/GraphExplorerSolidHandleFragment';
import {Box} from '../ui/Box';
import {Spinner} from '../ui/Spinner';

import {PipelineGraph} from './PipelineGraph';
import {asyncDagrePipelineLayout, getDagrePipelineLayout} from './getFullOpLayout';
import {IFullPipelineLayout} from './layout';
import {PipelineGraphOpFragment} from './types/PipelineGraphOpFragment';

const ASYNC_LAYOUT_SOLID_COUNT = 50;

interface Props {
  pipelineName: string;
  backgroundColor: string;
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

type State = {
  loading: boolean;
  layout: IFullPipelineLayout | null;
  layoutOpKey: string;
};

type Action =
  | {type: 'loading'}
  | {type: 'layout'; payload: {layout: IFullPipelineLayout; layoutOpKey: string}};

const reducer = (state: State, action: Action): State => {
  switch (action.type) {
    case 'loading':
      return {loading: true, layout: null, layoutOpKey: ''};
    case 'layout':
      return {
        loading: false,
        layout: action.payload.layout,
        layoutOpKey: action.payload.layoutOpKey,
      };
    default:
      return state;
  }
};

const initialState: State = {
  loading: false,
  layout: null,
  layoutOpKey: '',
};

export const PipelineGraphContainer: React.FC<Props> = (props) => {
  const {
    pipelineName,
    backgroundColor,
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
  const [state, dispatch] = React.useReducer(reducer, initialState);

  const parentOp = parentHandle && parentHandle.solid;
  const solidKey = ops.map((x) => x.name).join('|');
  const parentOpKey = parentOp && parentOp.name;

  React.useEffect(() => {
    async function delegateDagrePipelineLayout() {
      dispatch({type: 'loading'});
      const layout = await asyncDagrePipelineLayout(ops, parentOp);
      dispatch({
        type: 'layout',
        payload: {layout: layout as IFullPipelineLayout, layoutOpKey: solidKey},
      });
    }

    if (ops.length < ASYNC_LAYOUT_SOLID_COUNT) {
      const layout = getDagrePipelineLayout(ops, parentOp);
      dispatch({type: 'layout', payload: {layout, layoutOpKey: solidKey}});
    } else {
      delegateDagrePipelineLayout();
    }
  }, [solidKey, parentOpKey, ops, parentOp]);

  const {loading, layout, layoutOpKey} = state;
  if (loading || !layout || solidKey !== layoutOpKey) {
    return (
      <PipelineGraphLoading
        backgroundColor={backgroundColor}
        manyOps={ops.length > ASYNC_LAYOUT_SOLID_COUNT}
      />
    );
  }

  return (
    <PipelineGraph
      pipelineName={pipelineName}
      backgroundColor={backgroundColor}
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

const PipelineGraphLoading: React.FC<{backgroundColor: string; manyOps: boolean}> = (props) => {
  const {backgroundColor, manyOps} = props;
  return (
    <LoadingContainer $backgroundColor={backgroundColor}>
      {manyOps ? (
        <Box margin={{bottom: 24}}>Rendering a large number of ops, please wait…</Box>
      ) : null}
      <Spinner purpose="page" />
    </LoadingContainer>
  );
};

const LoadingContainer = styled.div<{$backgroundColor: string}>`
  background-color: ${({$backgroundColor}) => $backgroundColor};
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
`;
