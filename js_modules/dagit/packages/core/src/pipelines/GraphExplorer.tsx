import {gql} from '@apollo/client';
import {Breadcrumbs} from '@blueprintjs/core';
import {Checkbox, ColorsWIP, SplitPanelContainer, TextInput} from '@dagster-io/ui';
import Color from 'color';
import qs from 'qs';
import * as React from 'react';
import {Route} from 'react-router-dom';
import styled from 'styled-components/macro';

import {filterByQuery} from '../app/GraphQueryImpl';
import {PIPELINE_GRAPH_OP_FRAGMENT} from '../graph/PipelineGraph';
import {PipelineGraphContainer} from '../graph/PipelineGraphContainer';
import {OpNameOrPath} from '../ops/OpNameOrPath';
import {GraphQueryInput} from '../ui/GraphQueryInput';
import {RepoAddress} from '../workspace/types';

import {EmptyDAGNotice, LargeDAGNotice} from './GraphNotices';
import {NodeJumpBar} from './NodeJumpBar';
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
    setOptions,
    repoAddress,
    isGraph,
  } = props;
  const [nameMatch, setNameMatch] = React.useState('');

  const handleQueryChange = (opsQuery: string) => {
    onChangeExplorerPath({...explorerPath, opsQuery}, 'replace');
  };

  const handleAdjustPath = React.useMemo(
    () => (fn: (opNames: string[]) => void) => {
      const opNames = [...explorerPath.opNames];
      const retValue = fn(opNames);
      if (retValue !== undefined) {
        throw new Error('handleAdjustPath function is expected to mutate the array');
      }
      onChangeExplorerPath({...explorerPath, opNames}, 'push');
    },
    [onChangeExplorerPath, explorerPath],
  );

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

  const {opsQuery, opNames} = explorerPath;

  const selectedName = opNames[opNames.length - 1];
  const selectedHandle = handles.find((h) => selectedName === h.solid.name);

  // Run a few assertions on the state of the world and redirect the user
  // back to safety if they've landed in an invalid place. Note that we can
  // pop one layer at a time and this renders recursively until we reach a
  // valid parent.
  const invalidSelection = selectedName && !selectedHandle;
  const invalidParent =
    parentHandle && parentHandle.solid.definition.__typename !== 'CompositeSolidDefinition';

  React.useEffect(() => {
    if (invalidSelection || invalidParent) {
      handleAdjustPath((opNames) => opNames.pop());
    }
  }, [handleAdjustPath, invalidSelection, invalidParent]);

  const solids = React.useMemo(() => handles.map((h) => h.solid), [handles]);
  const solidsQueryEnabled = !parentHandle && !explorerPath.snapshotId;
  const explodeCompositesEnabled =
    !parentHandle &&
    (options.explodeComposites ||
      solids.some((f) => f.definition.__typename === 'CompositeSolidDefinition'));

  const queryResultOps = React.useMemo(
    () =>
      solidsQueryEnabled
        ? filterByQuery(solids, opsQuery)
        : {all: solids, focus: [], applyingEmptyDefault: false},
    [opsQuery, solids, solidsQueryEnabled],
  );

  const highlightedOps = React.useMemo(
    () => queryResultOps.all.filter((s) => s.name.toLowerCase().includes(nameMatch.toLowerCase())),
    [nameMatch, queryResultOps.all],
  );

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
              items={explorerPath.opNames.map((name, idx) => ({
                text: name,
                onClick: () =>
                  onChangeExplorerPath(
                    {...explorerPath, opNames: explorerPath.opNames.slice(0, idx + 1)},
                    'push',
                  ),
              }))}
              currentBreadcrumbRenderer={() => (
                <NodeJumpBar
                  nodes={queryResultOps.all}
                  nodeType="op"
                  selectedNode={selectedHandle && selectedHandle.solid}
                  onChange={handleClickOp}
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
                label="Explode graphs"
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
          {solids.length === 0 ? (
            <EmptyDAGNotice nodeType="op" isGraph={isGraph} />
          ) : queryResultOps.applyingEmptyDefault ? (
            <LargeDAGNotice nodeType="op" />
          ) : undefined}
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
                {...qs.parse(location.search || '', {ignoreQueryPrefix: true})}
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

export const RightInfoPanel = styled.div`
  // Fixes major perofmance hit. To reproduce, add enough content to
  // the sidebar that it scrolls (via overflow-y below) and then try
  // to pan the DAG.
  position: relative;

  height: 100%;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: ${ColorsWIP.White};
`;

export const RightInfoPanelContent = styled.div`
  flex: 1;
  overflow-y: auto;
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

const PipelineGraphQueryInputContainer = styled.div`
  z-index: 2;
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  white-space: nowrap;
`;
