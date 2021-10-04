import {gql} from '@apollo/client';
import {Breadcrumbs, Checkbox, InputGroup} from '@blueprintjs/core';
import Color from 'color';
import * as querystring from 'query-string';
import * as React from 'react';
import {Route} from 'react-router-dom';
import styled from 'styled-components/macro';

import {useFeatureFlags} from '../app/Flags';
import {filterByQuery} from '../app/GraphQueryImpl';
import {PIPELINE_GRAPH_SOLID_FRAGMENT} from '../graph/PipelineGraph';
import {PipelineGraphContainer} from '../graph/PipelineGraphContainer';
import {SolidNameOrPath} from '../solids/SolidNameOrPath';
import {ColorsWIP} from '../ui/Colors';
import {GraphQueryInput} from '../ui/GraphQueryInput';
import {IconWIP} from '../ui/Icon';
import {NonIdealState} from '../ui/NonIdealState';
import {SplitPanelContainer} from '../ui/SplitPanelContainer';
import {RepoAddress} from '../workspace/types';

import {SolidJumpBar} from './PipelineJumpComponents';
import {PipelineExplorerPath} from './PipelinePathUtils';
import {
  SidebarTabbedContainer,
  SIDEBAR_TABBED_CONTAINER_PIPELINE_FRAGMENT,
} from './SidebarTabbedContainer';
import {PipelineExplorerFragment} from './types/PipelineExplorerFragment';
import {PipelineExplorerSolidHandleFragment} from './types/PipelineExplorerSolidHandleFragment';

export interface PipelineExplorerOptions {
  explodeComposites: boolean;
}

interface PipelineExplorerProps {
  explorerPath: PipelineExplorerPath;
  onChangeExplorerPath: (path: PipelineExplorerPath, mode: 'replace' | 'push') => void;
  options: PipelineExplorerOptions;
  setOptions: (options: PipelineExplorerOptions) => void;
  pipeline: PipelineExplorerFragment;
  repoAddress?: RepoAddress;
  handles: PipelineExplorerSolidHandleFragment[];
  selectedHandle?: PipelineExplorerSolidHandleFragment;
  parentHandle?: PipelineExplorerSolidHandleFragment;
  getInvocations?: (definitionName: string) => {handleID: string}[];
}

export const PipelineExplorer: React.FC<PipelineExplorerProps> = (props) => {
  const {
    getInvocations,
    handles,
    options,
    pipeline,
    explorerPath,
    onChangeExplorerPath,
    parentHandle,
    selectedHandle,
    setOptions,
    repoAddress,
  } = props;
  const [highlighted, setHighlighted] = React.useState('');
  const {flagPipelineModeTuples} = useFeatureFlags();

  const handleQueryChange = (solidsQuery: string) => {
    onChangeExplorerPath({...explorerPath, solidsQuery}, 'replace');
  };

  const handleAdjustPath = (fn: (solidNames: string[]) => void) => {
    const pathSolids = [...explorerPath.pathSolids];
    const retValue = fn(pathSolids);
    if (retValue !== undefined) {
      throw new Error('handleAdjustPath function is expected to mutate the array');
    }
    onChangeExplorerPath({...explorerPath, pathSolids}, 'push');
  };

  // Note: this method handles relative solid paths, eg: {path: ['..', 'OtherSolid']}.
  // This is important because the DAG component tree doesn't always have access to a handleID,
  // and we sometimes want to be able to jump to a solid in the parent layer.
  //
  const handleClickSolid = (arg: SolidNameOrPath) => {
    handleAdjustPath((solidNames) => {
      if ('name' in arg) {
        solidNames[solidNames.length ? solidNames.length - 1 : 0] = arg.name;
      } else {
        if (arg.path[0] !== '..') {
          solidNames.length = 0;
        }
        if (arg.path[0] === '..' && solidNames[solidNames.length - 1] !== '') {
          solidNames.pop(); // remove the last path component indicating selection
        }
        while (arg.path[0] === '..') {
          arg.path.shift();
          solidNames.pop();
        }
        solidNames.push(...arg.path);
      }
    });
  };

  const handleEnterCompositeSolid = (arg: SolidNameOrPath) => {
    // To animate the rect of the composite solid expanding correctly, we need
    // to select it before entering it so we can draw the "initial state" of the
    // labeled rectangle.
    handleClickSolid(arg);

    window.requestAnimationFrame(() => {
      handleAdjustPath((solidNames) => {
        const last = 'name' in arg ? arg.name : arg.path[arg.path.length - 1];
        solidNames[solidNames.length - 1] = last;
        solidNames.push('');
      });
    });
  };

  const handleLeaveCompositeSolid = () => {
    handleAdjustPath((solidNames) => {
      solidNames.pop();
    });
  };

  const handleClickBackground = () => {
    handleClickSolid({name: ''});
  };

  const {solidsQuery} = explorerPath;
  const solids = React.useMemo(() => handles.map((h) => h.solid), [handles]);
  const solidsQueryEnabled = !parentHandle && !explorerPath.snapshotId;
  const explodeCompositesEnabled =
    !parentHandle &&
    (options.explodeComposites ||
      solids.some((f) => f.definition.__typename === 'CompositeSolidDefinition'));

  const queryResultSolids = React.useMemo(
    () => (solidsQueryEnabled ? filterByQuery(solids, solidsQuery) : {all: solids, focus: []}),
    [solidsQuery, solids, solidsQueryEnabled],
  );

  const {all} = queryResultSolids;
  const highlightedSolids = React.useMemo(() => all.filter((s) => s.name.includes(highlighted)), [
    highlighted,
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
              items={explorerPath.pathSolids.map((name, idx) => {
                return {
                  text: name,
                  onClick: () =>
                    onChangeExplorerPath(
                      {...explorerPath, pathSolids: explorerPath.pathSolids.slice(0, idx + 1)},
                      'push',
                    ),
                };
              })}
              currentBreadcrumbRenderer={() => (
                <SolidJumpBar
                  solids={queryResultSolids.all}
                  selectedSolid={selectedHandle && selectedHandle.solid}
                  onChange={(solid) => handleClickSolid({name: solid.name})}
                />
              )}
            />
          </PathOverlay>
          {solidsQueryEnabled && (
            <PipelineGraphQueryInputContainer>
              <GraphQueryInput
                items={solids}
                value={explorerPath.solidsQuery}
                placeholder={flagPipelineModeTuples ? 'Type an op subset' : 'Type a solid subset'}
                onChange={handleQueryChange}
              />
            </PipelineGraphQueryInputContainer>
          )}

          <SearchOverlay style={{background: backgroundTranslucent}}>
            <SolidHighlightInput
              type="text"
              name="highlighted"
              leftIcon="search"
              value={highlighted}
              placeholder="Highlight..."
              onChange={(e: React.ChangeEvent<any>) => setHighlighted(e.target.value)}
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
          {solids.length === 0 ? <EmptyDAGNotice /> : null}
          {solids.length > 0 &&
            queryResultSolids.all.length === 0 &&
            !explorerPath.solidsQuery.length && <LargeDAGNotice />}
          <PipelineGraphContainer
            pipelineName={pipeline.name}
            backgroundColor={backgroundColor}
            solids={queryResultSolids.all}
            focusSolids={queryResultSolids.focus}
            highlightedSolids={highlightedSolids}
            selectedHandle={selectedHandle}
            parentHandle={parentHandle}
            onClickSolid={handleClickSolid}
            onClickBackground={handleClickBackground}
            onEnterCompositeSolid={handleEnterCompositeSolid}
            onLeaveCompositeSolid={handleLeaveCompositeSolid}
          />
        </>
      }
      second={
        <RightInfoPanel>
          <Route
            // eslint-disable-next-line react/no-children-prop
            children={({location}: {location: any}) => (
              <SidebarTabbedContainer
                pipeline={pipeline}
                explorerPath={explorerPath}
                solidHandleID={selectedHandle && selectedHandle.handleID}
                parentSolidHandleID={parentHandle && parentHandle.handleID}
                getInvocations={getInvocations}
                onEnterCompositeSolid={handleEnterCompositeSolid}
                onClickSolid={handleClickSolid}
                repoAddress={repoAddress}
                {...querystring.parse(location.search || '')}
              />
            )}
          />
        </RightInfoPanel>
      }
    />
  );
};

export const PIPELINE_EXPLORER_FRAGMENT = gql`
  fragment PipelineExplorerFragment on IPipelineSnapshot {
    name
    description
    ...SidebarTabbedContainerPipelineFragment
  }
  ${SIDEBAR_TABBED_CONTAINER_PIPELINE_FRAGMENT}
`;

export const PIPELINE_EXPLORER_SOLID_HANDLE_FRAGMENT = gql`
  fragment PipelineExplorerSolidHandleFragment on SolidHandle {
    handleID
    solid {
      name
      ...PipelineGraphSolidFragment
    }
  }
  ${PIPELINE_GRAPH_SOLID_FRAGMENT}
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

const SearchOverlay = styled.div`
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

const SolidHighlightInput = styled(InputGroup)`
  margin-left: 7px;
  font-size: 14px;
  width: 220px;
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

const EmptyDAGNotice = () => {
  const {flagPipelineModeTuples} = useFeatureFlags();
  return (
    <NonIdealState
      icon="no-results"
      title={flagPipelineModeTuples ? 'Empty graph' : 'Empty pipeline'}
      description={
        <>
          <div>This {flagPipelineModeTuples ? 'graph' : 'pipeline'} is empty.</div>
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
