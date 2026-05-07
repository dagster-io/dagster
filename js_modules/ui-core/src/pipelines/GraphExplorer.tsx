// eslint-disable-next-line no-restricted-imports
import {Breadcrumbs} from '@blueprintjs/core';
import {Checkbox, ErrorBoundary, SplitPanelContainer, TextInput} from '@dagster-io/ui-components';
import qs from 'qs';
import {forwardRef, useEffect, useMemo, useState} from 'react';

import {
  CycleDetectedNotice,
  EmptyDAGNotice,
  EntirelyFilteredDAGNotice,
  LargeDAGNotice,
  LoadingNotice,
} from './GraphNotices';
import {ExplorerPath} from './PipelinePathUtils';
import {SIDEBAR_ROOT_CONTAINER_FRAGMENT} from './SidebarContainerOverview';
import {SidebarRoot} from './SidebarRoot';
import {gql} from '../apollo-client';
import {OpGraphSelectionInput} from './OpGraphSelectionInput';
import styles from './css/GraphExplorer.module.css';
import {GraphExplorerFragment, GraphExplorerSolidHandleFragment} from './types/GraphExplorer.types';
import {filterByQuery} from '../app/GraphQueryImpl';
import {Route} from '../app/Route';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {OP_GRAPH_OP_FRAGMENT, OpGraph} from '../graph/OpGraph';
import {useOpLayout} from '../graph/asyncGraphLayout';
import {filterOpSelectionByQuery} from '../op-selection/AntlrOpSelection';
import {OpNameOrPath} from '../ops/OpNameOrPath';
import {RepoAddress} from '../workspace/types';

export interface GraphExplorerOptions {
  explodeComposites: boolean;
  preferAssetRendering: boolean;
  isExternal?: boolean;
}

interface GraphExplorerProps {
  explorerPath: ExplorerPath;
  onChangeExplorerPath: (path: ExplorerPath, mode: 'replace' | 'push') => void;
  options: GraphExplorerOptions;
  setOptions: (options: GraphExplorerOptions) => void;
  container: GraphExplorerFragment;
  repoAddress?: RepoAddress;
  handles: GraphExplorerSolidHandleFragment[];
  parentHandle?: GraphExplorerSolidHandleFragment;
  getInvocations?: (definitionName: string) => {handleID: string}[];
  isGraph: boolean;
}

export const GraphExplorer = (props: GraphExplorerProps) => {
  const {
    getInvocations,
    handles,
    options,
    container,
    explorerPath,
    onChangeExplorerPath,
    parentHandle,
    setOptions,
    repoAddress,
    isGraph,
  } = props;
  const [nameMatch, setNameMatch] = useState('');

  const handleQueryChange = (opsQuery: string) => {
    onChangeExplorerPath({...explorerPath, opsQuery}, 'replace');
  };

  const handleAdjustPath = useMemo(
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
        if (arg.path[0] === '..') {
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
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        const last = 'name' in arg ? arg.name : arg.path[arg.path.length - 1]!;
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

  useEffect(() => {
    if (invalidSelection || invalidParent) {
      handleAdjustPath((opNames) => {
        opNames.pop();
      });
    }
  }, [handleAdjustPath, invalidSelection, invalidParent]);

  const solids = useMemo(() => handles.map((h) => h.solid), [handles]);
  const solidsQueryEnabled = !parentHandle && !explorerPath.snapshotId;
  const showAssetRenderingOption =
    !isGraph && solids.some((s) => s.definition.assetNodes.length > 0);
  const explodeCompositesEnabled =
    !parentHandle &&
    (options.explodeComposites ||
      solids.some((f) => f.definition.__typename === 'CompositeSolidDefinition'));

  const queryResultOps = useMemo(() => {
    if (solidsQueryEnabled) {
      return filterOpSelectionByQuery(solids, opsQuery);
    }
    return filterByQuery(solids, opsQuery);
  }, [opsQuery, solids, solidsQueryEnabled]);

  const highlightedOps = useMemo(
    () => queryResultOps.all.filter((s) => s.name.toLowerCase().includes(nameMatch.toLowerCase())),
    [nameMatch, queryResultOps.all],
  );

  const parentOp = parentHandle && parentHandle.solid;

  const [forceLargeGraph, setForceLargeGraph] = useState(false);
  const {layout, loading, async, error} = useOpLayout(
    queryResultOps.all,
    parentOp,
    forceLargeGraph,
  );

  const breadcrumbs = useMemo(() => {
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
      identifier="graph-explorer"
      firstInitialPercent={70}
      first={
        <ErrorBoundary region="op graph">
          {solidsQueryEnabled ? (
            <div className={styles.queryOverlay}>
              <OpGraphSelectionInput
                items={solids}
                value={explorerPath.opsQuery}
                onChange={handleQueryChange}
              />
            </div>
          ) : breadcrumbs.length > 1 ? (
            <div className={styles.breadcrumbsOverlay}>
              <Breadcrumbs currentBreadcrumbRenderer={() => <span />} items={breadcrumbs} />
            </div>
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

          <div className={styles.highlightOverlay}>
            <TextInput
              name="highlighted"
              icon="search"
              value={nameMatch}
              placeholder="Highlight…"
              onChange={(e) => setNameMatch(e.target.value)}
            />
          </div>

          {solids.length === 0 ? (
            <EmptyDAGNotice nodeType="op" isGraph={isGraph} />
          ) : Object.keys(queryResultOps.all).length === 0 ? (
            <EntirelyFilteredDAGNotice nodeType="op" />
          ) : error === 'cycles' ? (
            <CycleDetectedNotice />
          ) : error === 'too-large' ? (
            <LargeDAGNotice nodeType="op" setForceLargeGraph={setForceLargeGraph} />
          ) : undefined}

          {loading || !layout ? (
            <LoadingNotice async={async} nodeType="op" />
          ) : error ? null : (
            <OpGraph
              jobName={container.name}
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
              isExternal={options.isExternal}
            />
          )}
        </ErrorBoundary>
      }
      second={
        <RightInfoPanel>
          <Route
            // eslint-disable-next-line react/no-children-prop
            children={({location}: {location: any}) => (
              <SidebarRoot
                container={container}
                explorerPath={explorerPath}
                opHandleID={selectedHandle && selectedHandle.handleID}
                parentOpHandleID={parentHandle && parentHandle.handleID}
                getInvocations={getInvocations}
                onEnterSubgraph={handleEnterCompositeSolid}
                onClickOp={handleClickOp}
                repoAddress={repoAddress}
                isExternal={options.isExternal}
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
      ...GraphExplorerSolid
    }
  }

  fragment GraphExplorerSolid on Solid {
    name
    ...OpGraphOpFragment
  }

  ${OP_GRAPH_OP_FRAGMENT}
`;

export const RightInfoPanel = forwardRef<HTMLDivElement, React.ComponentProps<'div'>>(
  ({className, ...props}, ref) => (
    <div ref={ref} className={`${styles.rightInfoPanel} ${className ?? ''}`} {...props} />
  ),
);
RightInfoPanel.displayName = 'RightInfoPanel';

export const RightInfoPanelContent = forwardRef<HTMLDivElement, React.ComponentProps<'div'>>(
  ({className, ...props}, ref) => (
    <div ref={ref} className={`${styles.rightInfoPanelContent} ${className ?? ''}`} {...props} />
  ),
);
RightInfoPanelContent.displayName = 'RightInfoPanelContent';

export const OptionsOverlay = forwardRef<HTMLDivElement, React.ComponentProps<'div'>>(
  ({className, ...props}, ref) => (
    <div ref={ref} className={`${styles.optionsOverlay} ${className ?? ''}`} {...props} />
  ),
);
OptionsOverlay.displayName = 'OptionsOverlay';

export const QueryOverlay = forwardRef<HTMLDivElement, React.ComponentProps<'div'>>(
  ({className, ...props}, ref) => (
    <div ref={ref} className={`${styles.queryOverlay} ${className ?? ''}`} {...props} />
  ),
);
QueryOverlay.displayName = 'QueryOverlay';
