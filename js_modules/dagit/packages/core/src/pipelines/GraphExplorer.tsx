import {gql} from '@apollo/client';
import {Breadcrumbs} from '@blueprintjs/core';
import Color from 'color';
import * as querystring from 'query-string';
import * as React from 'react';
import {Route} from 'react-router-dom';
import styled from 'styled-components/macro';

import {filterByQuery} from '../app/GraphQueryImpl';
import {PIPELINE_GRAPH_OP_FRAGMENT} from '../graph/PipelineGraph';
import {PipelineGraphContainer} from '../graph/PipelineGraphContainer';
import {OpNameOrPath} from '../ops/OpNameOrPath';
import {Checkbox} from '../ui/Checkbox';
import {ColorsWIP} from '../ui/Colors';
import {GraphQueryInput} from '../ui/GraphQueryInput';
import {IconWIP} from '../ui/Icon';
import {NonIdealState} from '../ui/NonIdealState';
import {SplitPanelContainer} from '../ui/SplitPanelContainer';
import {TextInput} from '../ui/TextInput';
import {RepoAddress} from '../workspace/types';

import {OpJumpBar} from './PipelineJumpComponents';
import {ExplorerPath} from './PipelinePathUtils';
import {
  SidebarTabbedContainer,
  SIDEBAR_TABBED_CONTAINER_PIPELINE_FRAGMENT,
} from './SidebarTabbedContainer';
import {GraphExplorerFragment} from './types/GraphExplorerFragment';
import {GraphExplorerSolidHandleFragment} from './types/GraphExplorerSolidHandleFragment';

export interface GraphExplorerOptions {
  explodeComposites: boolean;
}

interface GraphExplorerProps {
  explorerPath: ExplorerPath;
  onChangeExplorerPath: (path: ExplorerPath, mode: 'replace' | 'push') => void;
  options: GraphExplorerOptions;
  setOptions: (options: GraphExplorerOptions) => void;
  pipelineOrGraph: GraphExplorerFragment;
  repoAddress?: RepoAddress;
  handles: GraphExplorerSolidHandleFragment[];
  selectedHandle?: GraphExplorerSolidHandleFragment;
  parentHandle?: GraphExplorerSolidHandleFragment;
  getInvocations?: (definitionName: string) => {handleID: string}[];
  isGraph: boolean;
}

export const GraphExplorer: React.FC<GraphExplorerProps> = (props) => {
  const {
    getInvocations,
    handles,
    options,
    pipelineOrGraph,
    explorerPath,
    onChangeExplorerPath,
    parentHandle,
    selectedHandle,
    setOptions,
    repoAddress,
    isGraph,
  } = props;
  const [nameMatch, setNameMatch] = React.useState('');

  const handleQueryChange = (opsQuery: string) => {
    onChangeExplorerPath({...explorerPath, opsQuery}, 'replace');
  };

  const handleAdjustPath = (fn: (opNames: string[]) => void) => {
    const opNames = [...explorerPath.opNames];
    const retValue = fn(opNames);
    if (retValue !== undefined) {
      throw new Error('handleAdjustPath function is expected to mutate the array');
    }
    onChangeExplorerPath({...explorerPath, opNames}, 'push');
  };

  // Note: this method handles relative solid paths, eg: {path: ['..', 'OtherSolid']}.
  // This is important because the DAG component tree doesn't always have access to a handleID,
  // and we sometimes want to be able to jump to a solid in the parent layer.
  //
  const handleClickOp = (arg: OpNameOrPath) => {
    handleAdjustPath((opNames) => {
      if ('name' in arg) {
        opNames[opNames.length ? opNames.length - 1 : 0] = arg.name;
      } else {
        if (arg.path[0] !== '..') {
          opNames.length = 0;
        }
        if (arg.path[0] === '..' && opNames[opNames.length - 1] !== '') {
          opNames.pop(); // remove the last path component indicating selection
        }
        while (arg.path[0] === '..') {
          arg.path.shift();
          opNames.pop();
        }
        opNames.push(...arg.path);
      }
    });
  };

  const handleEnterCompositeSolid = (arg: OpNameOrPath) => {
    // To animate the rect of the composite solid expanding correctly, we need
    // to select it before entering it so we can draw the "initial state" of the
    // labeled rectangle.
    handleClickOp(arg);

    window.requestAnimationFrame(() => {
      handleAdjustPath((opNames) => {
        const last = 'name' in arg ? arg.name : arg.path[arg.path.length - 1];
        opNames[opNames.length - 1] = last;
        opNames.push('');
      });
    });
  };

  const handleLeaveCompositeSolid = () => {
    handleAdjustPath((opNames) => {
      opNames.pop();
    });
  };

  const handleClickBackground = () => {
    handleClickOp({name: ''});
  };

  const {opsQuery} = explorerPath;
  const solids = React.useMemo(() => handles.map((h) => h.solid), [handles]);
  const solidsQueryEnabled = !parentHandle && !explorerPath.snapshotId;
  const explodeCompositesEnabled =
    !parentHandle &&
    (options.explodeComposites ||
      solids.some((f) => f.definition.__typename === 'CompositeSolidDefinition'));

  const queryResultOps = React.useMemo(
    () => (solidsQueryEnabled ? filterByQuery(solids, opsQuery) : {all: solids, focus: []}),
    [opsQuery, solids, solidsQueryEnabled],
  );

  const {all} = queryResultOps;
  const highlightedOps = React.useMemo(() => all.filter((s) => s.name.includes(nameMatch)), [
    nameMatch,
    all,
  ]);

  const backgroundColor = parentHandle ? ColorsWIP.White : ColorsWIP.White;
  const backgroundTranslucent = Color(backgroundColor).fade(0.6).toString();

  return (
    <SplitPanelContainer
      identifier="explorer"
      firstInitialPercent={70}
      first={
        <>
          <PathOverlay style={{background: backgroundTranslucent}}>
            <Breadcrumbs
              items={explorerPath.opNames.map((name, idx) => {
                return {
                  text: name,
                  onClick: () =>
                    onChangeExplorerPath(
                      {...explorerPath, opNames: explorerPath.opNames.slice(0, idx + 1)},
                      'push',
                    ),
                };
              })}
              currentBreadcrumbRenderer={() => (
                <OpJumpBar
                  ops={queryResultOps.all}
                  selectedOp={selectedHandle && selectedHandle.solid}
                  onChange={(solid) => handleClickOp({name: solid.name})}
                />
              )}
            />
          </PathOverlay>
          {solidsQueryEnabled && (
            <PipelineGraphQueryInputContainer>
              <GraphQueryInput
                items={solids}
                value={explorerPath.opsQuery}
                placeholder="Type an op subset…"
                onChange={handleQueryChange}
              />
            </PipelineGraphQueryInputContainer>
          )}

          <SearchOverlay style={{background: backgroundTranslucent}}>
            <TextInput
              name="highlighted"
              icon="search"
              value={nameMatch}
              placeholder="Highlight…"
              onChange={(e) => setNameMatch(e.target.value)}
            />
          </SearchOverlay>
          {explodeCompositesEnabled && (
            <OptionsOverlay>
              <Checkbox
                label="Explode composites"
                checked={options.explodeComposites}
                onChange={() => {
                  handleQueryChange('');
                  setOptions({
                    ...options,
                    explodeComposites: !options.explodeComposites,
                  });
                }}
              />
            </OptionsOverlay>
          )}
          {solids.length === 0 ? <EmptyDAGNotice isGraph={isGraph} /> : null}
          {solids.length > 0 &&
            queryResultOps.all.length === 0 &&
            !explorerPath.opsQuery.length && <LargeDAGNotice />}
          <PipelineGraphContainer
            pipelineName={pipelineOrGraph.name}
            backgroundColor={backgroundColor}
            ops={queryResultOps.all}
            focusOps={queryResultOps.focus}
            highlightedOps={highlightedOps}
            selectedHandle={selectedHandle}
            parentHandle={parentHandle}
            onClickOp={handleClickOp}
            onClickBackground={handleClickBackground}
            onEnterSubgraph={handleEnterCompositeSolid}
            onLeaveSubgraph={handleLeaveCompositeSolid}
          />
        </>
      }
      second={
        <RightInfoPanel>
          <Route
            // eslint-disable-next-line react/no-children-prop
            children={({location}: {location: any}) => (
              <SidebarTabbedContainer
                pipeline={pipelineOrGraph}
                explorerPath={explorerPath}
                opHandleID={selectedHandle && selectedHandle.handleID}
                parentOpHandleID={parentHandle && parentHandle.handleID}
                getInvocations={getInvocations}
                onEnterSubgraph={handleEnterCompositeSolid}
                onClickOp={handleClickOp}
                repoAddress={repoAddress}
                isGraph={isGraph}
                {...querystring.parse(location.search || '')}
              />
            )}
          />
        </RightInfoPanel>
      }
    />
  );
};

export const GRAPH_EXPLORER_FRAGMENT = gql`
  fragment GraphExplorerFragment on SolidContainer {
    id
    name
    description
    ...SidebarTabbedContainerPipelineFragment
  }
  ${SIDEBAR_TABBED_CONTAINER_PIPELINE_FRAGMENT}
`;

export const GRAPH_EXPLORER_SOLID_HANDLE_FRAGMENT = gql`
  fragment GraphExplorerSolidHandleFragment on SolidHandle {
    handleID
    solid {
      name
      ...PipelineGraphOpFragment
    }
  }
  ${PIPELINE_GRAPH_OP_FRAGMENT}
`;

const RightInfoPanel = styled.div`
  // Fixes major perofmance hit. To reproduce, add enough content to
  // the sidebar that it scrolls (via overflow-y below) and then try
  // to pan the DAG.
  position: relative;

  height: 100%;
  overflow-y: scroll;
  background: ${ColorsWIP.White};
`;

const OptionsOverlay = styled.div`
  z-index: 2;
  padding: 5px 15px;
  display: inline-flex;
  align-items: stretch;
  position: absolute;
  bottom: 0;
  left: 0;
`;

export const SearchOverlay = styled.div`
  z-index: 2;
  padding: 12px 12px 0 0;
  display: inline-flex;
  align-items: stretch;
  position: absolute;
  top: 0;
  right: 0;
`;

const PathOverlay = styled.div`
  z-index: 2;
  padding: 12px 0 0 20px;
  max-width: calc(100% - 250px);
  display: inline-flex;
  align-items: center;
  position: absolute;
  left: 0;
`;

const LargeDAGNotice = () => (
  <LargeDAGContainer>
    <LargeDAGInstructionBox>
      <p>
        This is a large DAG that may be difficult to visualize. Type <code>*</code> in the subset
        box below to render the entire thing, or type a solid name and use:
      </p>
      <ul style={{marginBottom: 0}}>
        <li>
          <code>+</code> to expand a single layer before or after the solid.
        </li>
        <li>
          <code>*</code> to expand recursively before or after the solid.
        </li>
        <li>
          <code>AND</code> to render another disconnected fragment.
        </li>
      </ul>
    </LargeDAGInstructionBox>
    <IconWIP name="arrow_downward" size={24} />
  </LargeDAGContainer>
);

const EmptyDAGNotice: React.FC<{isGraph: boolean}> = ({isGraph}) => {
  return (
    <NonIdealState
      icon="no-results"
      title={isGraph ? 'Empty graph' : 'Empty pipeline'}
      description={
        <>
          <div>This {isGraph ? 'graph' : 'pipeline'} is empty.</div>
          <div>Solids will appear here when you add them.</div>
        </>
      }
    />
  );
};

const LargeDAGContainer = styled.div`
  width: 50vw;
  position: absolute;
  transform: translateX(-50%);
  left: 50%;
  bottom: 60px;
  z-index: 2;
  max-width: 600px;
  text-align: center;
  .bp3-icon {
    color: ${ColorsWIP.Gray200};
  }
`;

const LargeDAGInstructionBox = styled.div`
  padding: 15px 20px;
  border: 1px solid #fff5c3;
  margin-bottom: 20px;
  color: ${ColorsWIP.Gray800};
  background: #fffbe5;
  text-align: left;
  line-height: 1.4rem;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  code {
    background: #f8ebad;
    font-weight: 500;
    padding: 0 4px;
  }
`;

const PipelineGraphQueryInputContainer = styled.div`
  z-index: 2;
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  white-space: nowrap;
`;
