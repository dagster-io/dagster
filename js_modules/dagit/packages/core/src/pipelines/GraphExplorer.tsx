import {gql} from '@apollo/client';
// eslint-disable-next-line no-restricted-imports
import {Breadcrumbs} from '@blueprintjs/core';
import {Checkbox, Colors, SplitPanelContainer, TextInput} from '@dagster-io/ui';
import Color from 'color';
import qs from 'qs';
import * as React from 'react';
import {Route} from 'react-router-dom';
import styled from 'styled-components/macro';

import {filterByQuery} from '../app/GraphQueryImpl';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {OpGraph, OP_GRAPH_OP_FRAGMENT} from '../graph/OpGraph';
import {useOpLayout} from '../graph/asyncGraphLayout';
import {OpNameOrPath} from '../ops/OpNameOrPath';
import {GraphQueryInput} from '../ui/GraphQueryInput';
import {RepoAddress} from '../workspace/types';

import {
  EmptyDAGNotice,
  EntirelyFilteredDAGNotice,
  LargeDAGNotice,
  LoadingNotice,
} from './GraphNotices';
import {ExplorerPath} from './PipelinePathUtils';
import {SidebarRoot, SIDEBAR_ROOT_CONTAINER_FRAGMENT} from './SidebarRoot';
import {GraphExplorerFragment} from './types/GraphExplorerFragment';
import {GraphExplorerSolidHandleFragment} from './types/GraphExplorerSolidHandleFragment';

export interface GraphExplorerOptions {
  explodeComposites: boolean;
  preferAssetRendering: boolean;
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
        throw new Error(
          'handleAdjustPath function is expected to mutate the array and return nothing',
        );
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
      handleAdjustPath((opNames) => {
        opNames.pop();
      });
    }
  }, [handleAdjustPath, invalidSelection, invalidParent]);

  const solids = React.useMemo(() => handles.map((h) => h.solid), [handles]);
  const solidsQueryEnabled = !parentHandle && !explorerPath.snapshotId;
  const showAssetRenderingOption =
    !isGraph && solids.some((s) => s.definition.assetNodes.length > 0);
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

  const parentOp = parentHandle && parentHandle.solid;
  const {layout, loading, async} = useOpLayout(queryResultOps.all, parentOp);

  const breadcrumbs = React.useMemo(() => {
    const opNames = explorerPath.opNames;
    const breadcrumbs = opNames.map((name, idx) => ({
      text: name,
      onClick: () => {
        onChangeExplorerPath({...explorerPath, opNames: opNames.slice(0, idx + 1)}, 'push');
      },
    }));
    // If you're viewing a graph that is part of an asset job, we don't want to let you view
    // the "root" graph becacuse it's not something you defined explicitly. Remove the first item.
    if (isHiddenAssetGroupJob(explorerPath.pipelineName)) {
      breadcrumbs.shift();
    }
    return breadcrumbs;
  }, [explorerPath, onChangeExplorerPath]);

  return (
    <SplitPanelContainer
      identifier="explorer"
      firstInitialPercent={70}
      first={
        <>
          {solidsQueryEnabled ? (
            <QueryOverlay>
              <GraphQueryInput
                items={solids}
                value={explorerPath.opsQuery}
                placeholder="Type an op subset…"
                popoverPosition="bottom-left"
                onChange={handleQueryChange}
              />
            </QueryOverlay>
          ) : breadcrumbs.length > 1 ? (
            <BreadcrumbsOverlay>
              <Breadcrumbs currentBreadcrumbRenderer={() => <span />} items={breadcrumbs} />
            </BreadcrumbsOverlay>
          ) : null}

          {(showAssetRenderingOption || explodeCompositesEnabled) && (
            <OptionsOverlay>
              {showAssetRenderingOption && (
                <Checkbox
                  format="switch"
                  label="View as Asset Graph"
                  checked={options.preferAssetRendering}
                  onChange={() => {
                    onChangeExplorerPath({...explorerPath, opNames: []}, 'replace');
                    setOptions({
                      ...options,
                      preferAssetRendering: !options.preferAssetRendering,
                    });
                  }}
                />
              )}
              {explodeCompositesEnabled && (
                <Checkbox
                  format="switch"
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
              )}
            </OptionsOverlay>
          )}

          <HighlightOverlay>
            <TextInput
              name="highlighted"
              icon="search"
              value={nameMatch}
              placeholder="Highlight…"
              onChange={(e) => setNameMatch(e.target.value)}
            />
          </HighlightOverlay>

          {solids.length === 0 ? (
            <EmptyDAGNotice nodeType="op" isGraph={isGraph} />
          ) : queryResultOps.applyingEmptyDefault ? (
            <LargeDAGNotice nodeType="op" />
          ) : Object.keys(queryResultOps.all).length === 0 ? (
            <EntirelyFilteredDAGNotice nodeType="op" />
          ) : undefined}

          {loading || !layout ? (
            <LoadingNotice async={async} nodeType="op" />
          ) : (
            <OpGraph
              jobName={pipelineOrGraph.name}
              ops={queryResultOps.all}
              focusOps={queryResultOps.focus}
              highlightedOps={highlightedOps}
              selectedHandleID={selectedHandle && selectedHandle.handleID}
              selectedOp={selectedHandle && selectedHandle.solid}
              parentHandleID={parentHandle && parentHandle.handleID}
              parentOp={parentOp}
              onClickOp={handleClickOp}
              onClickBackground={handleClickBackground}
              onEnterSubgraph={handleEnterCompositeSolid}
              onLeaveSubgraph={handleLeaveCompositeSolid}
              layout={layout}
            />
          )}
        </>
      }
      second={
        <RightInfoPanel>
          <Route
            // eslint-disable-next-line react/no-children-prop
            children={({location}: {location: any}) => (
              <SidebarRoot
                container={pipelineOrGraph}
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
    ...SidebarRootContainerFragment
  }
  ${SIDEBAR_ROOT_CONTAINER_FRAGMENT}
`;

export const GRAPH_EXPLORER_ASSET_NODE_FRAGMENT = gql`
  fragment GraphExplorerAssetNodeFragment on AssetNode {
    id
    opNames
    assetKey {
      path
    }
  }
`;

export const GRAPH_EXPLORER_SOLID_HANDLE_FRAGMENT = gql`
  fragment GraphExplorerSolidHandleFragment on SolidHandle {
    handleID
    solid {
      name
      ...OpGraphOpFragment
    }
  }
  ${OP_GRAPH_OP_FRAGMENT}
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
  background: ${Colors.White};
`;

export const RightInfoPanelContent = styled.div`
  flex: 1;
  overflow-y: auto;
`;

export const OptionsOverlay = styled.div`
  background-color: ${Color(Colors.White).fade(0.6).toString()};
  z-index: 2;
  padding: 15px 20px;
  display: inline-flex;
  align-items: stretch;
  white-space: nowrap;
  position: absolute;
  bottom: 0;
  left: 0;
  gap: 8px;
`;

export const HighlightOverlay = styled.div`
  background-color: ${Color(Colors.White).fade(0.6).toString()};
  z-index: 2;
  padding: 8px 12px 0 0;
  display: inline-flex;
  align-items: stretch;
  position: absolute;
  top: 0;
  right: 0;
`;

export const QueryOverlay = styled.div`
  z-index: 2;
  position: absolute;
  top: 8px;
  left: 24px;
  white-space: nowrap;
  display: flex;
  gap: 10px;
`;

export const BreadcrumbsOverlay = styled.div`
  background-color: ${Color(Colors.White).fade(0.6).toString()};
  z-index: 2;
  padding: 12px 0 0 20px;
  height: 42px;
  max-width: calc(100% - 250px);
  display: inline-flex;
  align-items: center;
  position: absolute;
  top: 0;
  left: 0;
`;
