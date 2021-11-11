import * as React from 'react';
import styled from 'styled-components/macro';

import {GraphExplorerSolidHandleFragment} from '../pipelines/types/GraphExplorerSolidHandleFragment';
import {SolidNameOrPath} from '../solids/SolidNameOrPath';
import {Box} from '../ui/Box';
import {Spinner} from '../ui/Spinner';

import {PipelineGraph} from './PipelineGraph';
import {asyncDagrePipelineLayout, getDagrePipelineLayout} from './getFullSolidLayout';
import {IFullPipelineLayout} from './layout';
import {PipelineGraphSolidFragment} from './types/PipelineGraphSolidFragment';

const ASYNC_LAYOUT_SOLID_COUNT = 50;

interface Props {
  pipelineName: string;
  backgroundColor: string;
  solids: PipelineGraphSolidFragment[];
  focusSolids: PipelineGraphSolidFragment[];
  highlightedSolids: PipelineGraphSolidFragment[];
  selectedHandle?: GraphExplorerSolidHandleFragment;
  parentHandle?: GraphExplorerSolidHandleFragment;
  onClickSolid?: (arg: SolidNameOrPath) => void;
  onEnterCompositeSolid?: (arg: SolidNameOrPath) => void;
  onLeaveCompositeSolid?: () => void;
  onClickBackground?: () => void;
}

type State = {
  loading: boolean;
  layout: IFullPipelineLayout | null;
  layoutSolidKey: string;
};

type Action =
  | {type: 'loading'}
  | {type: 'layout'; payload: {layout: IFullPipelineLayout; layoutSolidKey: string}};

const reducer = (state: State, action: Action): State => {
  switch (action.type) {
    case 'loading':
      return {loading: true, layout: null, layoutSolidKey: ''};
    case 'layout':
      return {
        loading: false,
        layout: action.payload.layout,
        layoutSolidKey: action.payload.layoutSolidKey,
      };
    default:
      return state;
  }
};

const initialState: State = {
  loading: false,
  layout: null,
  layoutSolidKey: '',
};

export const PipelineGraphContainer: React.FC<Props> = (props) => {
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
  const [state, dispatch] = React.useReducer(reducer, initialState);

  const parentSolid = parentHandle && parentHandle.solid;
  const solidKey = solids.map((x) => x.name).join('|');
  const parentSolidKey = parentSolid && parentSolid.name;

  React.useEffect(() => {
    async function delegateDagrePipelineLayout() {
      dispatch({type: 'loading'});
      const layout = await asyncDagrePipelineLayout(solids, parentSolid);
      dispatch({
        type: 'layout',
        payload: {layout: layout as IFullPipelineLayout, layoutSolidKey: solidKey},
      });
    }

    if (solids.length < ASYNC_LAYOUT_SOLID_COUNT) {
      const layout = getDagrePipelineLayout(solids, parentSolid);
      dispatch({type: 'layout', payload: {layout, layoutSolidKey: solidKey}});
    } else {
      delegateDagrePipelineLayout();
    }
  }, [solidKey, parentSolidKey, solids, parentSolid]);

  const {loading, layout, layoutSolidKey} = state;
  if (loading || !layout || solidKey !== layoutSolidKey) {
    return (
      <PipelineGraphLoading
        backgroundColor={backgroundColor}
        manySolids={solids.length > ASYNC_LAYOUT_SOLID_COUNT}
      />
    );
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
};

const PipelineGraphLoading: React.FC<{backgroundColor: string; manySolids: boolean}> = (props) => {
  const {backgroundColor, manySolids} = props;
  return (
    <LoadingContainer $backgroundColor={backgroundColor}>
      {manySolids ? (
        <Box margin={{bottom: 24}}>Rendering a large number of solids, please wait…</Box>
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
