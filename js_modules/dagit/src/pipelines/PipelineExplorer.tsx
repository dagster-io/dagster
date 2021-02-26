import {gql} from '@apollo/client';
import {Breadcrumbs, Checkbox, Colors, Icon, InputGroup, NonIdealState} from '@blueprintjs/core';
import Color from 'color';
import {History} from 'history';
import * as querystring from 'query-string';
import * as React from 'react';
import {Route} from 'react-router';
import styled from 'styled-components/macro';

import {filterByQuery} from 'src/app/GraphQueryImpl';
import {PIPELINE_GRAPH_SOLID_FRAGMENT} from 'src/graph/PipelineGraph';
import {PipelineGraphContainer} from 'src/graph/PipelineGraphContainer';
import {SolidJumpBar} from 'src/pipelines/PipelineJumpComponents';
import {PipelineExplorerPath, explorerPathToString} from 'src/pipelines/PipelinePathUtils';
import {
  SidebarTabbedContainer,
  SIDEBAR_TABBED_CONTAINER_PIPELINE_FRAGMENT,
} from 'src/pipelines/SidebarTabbedContainer';
import {PipelineExplorerFragment} from 'src/pipelines/types/PipelineExplorerFragment';
import {PipelineExplorerSolidHandleFragment} from 'src/pipelines/types/PipelineExplorerSolidHandleFragment';
import {SolidNameOrPath} from 'src/solids/SolidNameOrPath';
import {GraphQueryInput} from 'src/ui/GraphQueryInput';
import {SplitPanelContainer} from 'src/ui/SplitPanelContainer';
import {RepoAddress} from 'src/workspace/types';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

export interface PipelineExplorerOptions {
  explodeComposites: boolean;
}

interface PipelineExplorerProps {
  history: History;
  explorerPath: PipelineExplorerPath;
  options: PipelineExplorerOptions;
  setOptions: (options: PipelineExplorerOptions) => void;
  pipeline: PipelineExplorerFragment;
  repoAddress?: RepoAddress;
  handles: PipelineExplorerSolidHandleFragment[];
  selectedHandle?: PipelineExplorerSolidHandleFragment;
  parentHandle?: PipelineExplorerSolidHandleFragment;
  getInvocations?: (definitionName: string) => {handleID: string}[];
}

interface PipelineExplorerState {
  highlighted: string;
}

export class PipelineExplorer extends React.Component<
  PipelineExplorerProps,
  PipelineExplorerState
> {
  pathOverlayEl = React.createRef<HTMLDivElement>();

  state = {
    highlighted: '',
  };

  handleQueryChange = (solidsQuery: string) => {
    const {history, explorerPath} = this.props;
    history.replace(this.buildPath(explorerPathToString({...explorerPath, solidsQuery})));
  };

  handleAdjustPath = (fn: (solidNames: string[]) => void) => {
    const {history, explorerPath} = this.props;
    const pathSolids = [...explorerPath.pathSolids];
    const retValue = fn(pathSolids);
    if (retValue !== undefined) {
      throw new Error('handleAdjustPath function is expected to mutate the array');
    }
    history.push(this.buildPath(explorerPathToString({...explorerPath, pathSolids})));
  };

  // Note: this method handles relative solid paths, eg: {path: ['..', 'OtherSolid']}.
  // This is important because the DAG component tree doesn't always have access to a handleID,
  // and we sometimes want to be able to jump to a solid in the parent layer.
  //
  handleClickSolid = (arg: SolidNameOrPath) => {
    this.handleAdjustPath((solidNames) => {
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

  handleEnterCompositeSolid = (arg: SolidNameOrPath) => {
    // To animate the rect of the composite solid expanding correctly, we need
    // to select it before entering it so we can draw the "initial state" of the
    // labeled rectangle.
    this.handleClickSolid(arg);

    window.requestAnimationFrame(() => {
      this.handleAdjustPath((solidNames) => {
        const last = 'name' in arg ? arg.name : arg.path[arg.path.length - 1];
        solidNames[solidNames.length - 1] = last;
        solidNames.push('');
      });
    });
  };

  handleLeaveCompositeSolid = () => {
    this.handleAdjustPath((solidNames) => {
      solidNames.pop();
    });
  };

  handleClickBackground = () => {
    this.handleClickSolid({name: ''});
  };

  buildPath = (path: string) => {
    const {explorerPath, repoAddress} = this.props;
    const {snapshotId} = explorerPath;
    if (snapshotId) {
      return `/instance/snapshots/${path}`;
    }
    if (repoAddress) {
      return workspacePathFromAddress(repoAddress, `/pipelines/${path}`);
    }
    return `/workspace/pipelines/${path}`;
  };

  render() {
    const {options, pipeline, explorerPath, parentHandle, selectedHandle} = this.props;
    const {highlighted} = this.state;

    const solids = this.props.handles.map((h) => h.solid);
    const solidsQueryEnabled = !parentHandle && !explorerPath.snapshotId;
    const explodeCompositesEnabled =
      !parentHandle &&
      (options.explodeComposites ||
        solids.some((f) => f.definition.__typename === 'CompositeSolidDefinition'));

    const queryResultSolids = solidsQueryEnabled
      ? filterByQuery(solids, explorerPath.solidsQuery)
      : {all: solids, focus: []};

    const highlightedSolids = queryResultSolids.all.filter((s) => s.name.includes(highlighted));

    const backgroundColor = parentHandle ? Colors.WHITE : Colors.WHITE;
    const backgroundTranslucent = Color(backgroundColor).fade(0.6).toString();

    return (
      <SplitPanelContainer
        identifier="explorer"
        firstInitialPercent={70}
        first={
          <>
            <PathOverlay style={{background: backgroundTranslucent}} ref={this.pathOverlayEl}>
              <Breadcrumbs
                items={explorerPath.pathSolids.map((name, idx) => {
                  return {
                    text: name,
                    href: this.buildPath(
                      explorerPathToString({
                        ...explorerPath,
                        pathSolids: explorerPath.pathSolids.slice(0, idx + 1),
                      }),
                    ),
                  };
                })}
                currentBreadcrumbRenderer={() => (
                  <SolidJumpBar
                    solids={queryResultSolids.all}
                    selectedSolid={selectedHandle && selectedHandle.solid}
                    onChange={(solid) => this.handleClickSolid({name: solid.name})}
                  />
                )}
              />
            </PathOverlay>
            {solidsQueryEnabled && (
              <PipelineGraphQueryInputContainer>
                <GraphQueryInput
                  items={solids}
                  value={explorerPath.solidsQuery}
                  placeholder="Type a Solid Subset"
                  onChange={this.handleQueryChange}
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
                onChange={(e: React.ChangeEvent<any>) =>
                  this.setState({highlighted: e.target.value})
                }
              />
            </SearchOverlay>
            {explodeCompositesEnabled && (
              <OptionsOverlay>
                <Checkbox
                  label="Explode composites"
                  checked={options.explodeComposites}
                  onChange={() => {
                    this.handleQueryChange('');
                    this.props.setOptions({
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
              onClickSolid={this.handleClickSolid}
              onClickBackground={this.handleClickBackground}
              onEnterCompositeSolid={this.handleEnterCompositeSolid}
              onLeaveCompositeSolid={this.handleLeaveCompositeSolid}
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
                  getInvocations={this.props.getInvocations}
                  onEnterCompositeSolid={this.handleEnterCompositeSolid}
                  onClickSolid={this.handleClickSolid}
                  {...querystring.parse(location.search || '')}
                />
              )}
            />
          </RightInfoPanel>
        }
      />
    );
  }
}

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
  background: ${Colors.WHITE};
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
    <Icon icon="arrow-down" iconSize={40} />
  </LargeDAGContainer>
);

const EmptyDAGNotice = () => (
  <NonIdealState
    icon="diagram-tree"
    title="Empty pipeline"
    description={
      <>
        <div>This pipeline is empty.</div>
        <div>Solids will appear here when you add them.</div>
      </>
    }
  />
);

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
    color: ${Colors.LIGHT_GRAY1};
  }
`;

const LargeDAGInstructionBox = styled.div`
  padding: 15px 20px;
  border: 1px solid #fff5c3;
  margin-bottom: 20px;
  color: ${Colors.DARK_GRAY3};
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
