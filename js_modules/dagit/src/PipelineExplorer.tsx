import * as React from "react";
import gql from "graphql-tag";
import Color from "color";
import styled from "styled-components";
import { History } from "history";
import { Icon, Colors } from "@blueprintjs/core";
import { Route } from "react-router";
import { Link } from "react-router-dom";
import * as querystring from "query-string";

import { PipelineExplorerFragment } from "./types/PipelineExplorerFragment";
import PipelineGraph from "./graph/PipelineGraph";
import { SplitPanelChildren } from "./SplitPanelChildren";
import SidebarTabbedContainer from "./SidebarTabbedContainer";
import { SolidJumpBar } from "./PipelineJumpComponents";
import {
  PipelineExplorerSolidHandleFragment,
  PipelineExplorerSolidHandleFragment_solid
} from "./types/PipelineExplorerSolidHandleFragment";
import {
  getDagrePipelineLayout,
  IFullPipelineLayout
} from "./graph/getFullSolidLayout";

interface IPipelineExplorerProps {
  history: History;
  path: string[];
  pipeline: PipelineExplorerFragment;
  handles: PipelineExplorerSolidHandleFragment[];
  selectedHandle?: PipelineExplorerSolidHandleFragment;
  selectedDefinitionInvocations?: { handleID: string }[];
  parentHandle?: PipelineExplorerSolidHandleFragment;
}

interface IPipelineExplorerState {
  filter: string;
}

class AdjacencyMatrix {
  adjacencyMatrix: Array<Array<boolean>>;
  // TODO: One reason doing DFS on the client side is sub optimal.
  // javascript is tail end recursive tho so we could go for ever without worrying about
  // stack overflow problems?

  constructor(adjacencyMatrix: Array<Array<boolean>>) {
    this.adjacencyMatrix = adjacencyMatrix;
  }

  getParents(index: number) {
    const parents = new Array<number>();
    // It is impossible to specify yourself as an input dependency because this is a DAG so X[i, i]
    // will always be 0.
    this.adjacencyMatrix[index].forEach((candidateParent, index) => {
      if (candidateParent) {
        parents.push(index);
      }
    });
    return parents;
  }

  getChildren(index: number) {
    const children = new Array<number>();
    this.adjacencyMatrix
      .map(row => row[index])
      .forEach((candidateChild, index) => {
        if (candidateChild) {
          children.push(index);
        }
      });
    return children;
  }

  search(includeParents: boolean, initialCandidates: number[]) {
    const results = new Set<number>();
    const stack = [...initialCandidates];
    while (stack.length !== 0) {
      // pop off stack and add to upstreamDependency list
      const node = stack.shift();
      if (node !== undefined) {
        results.add(node);
        const next = includeParents
          ? this.getParents(node)
          : this.getChildren(node);
        next.forEach(element => {
          stack.unshift(element);
        });
      }
    }
    return Array.from(results);
  }

  fetchUpstream(index: number) {
    return Array.from(this.search(true, this.getParents(index)));
  }

  fetchDownstream(index: number) {
    return Array.from(this.search(false, this.getChildren(index)));
  }
}

export function createAdjacencyMatrix(
  solids: PipelineExplorerSolidHandleFragment_solid[],
  memo: WeakMap<PipelineExplorerSolidHandleFragment_solid[], AdjacencyMatrix>
) {
  // Done because typescript was not autoresolving .has
  const memoizedMatrix = memo.get(solids);
  if (memoizedMatrix !== undefined) {
    return memoizedMatrix;
  }
  // TODO: Consider alternatives to making this sparse because this will blow up if solids.length is large.
  const adjacencyMatrix = Array.from(Array(solids.length), _ =>
    Array(solids.length).fill(false)
  );
  const indexMap = new Map();
  solids.forEach((solid, index) => {
    indexMap.set(solid.name, index);
  });

  solids.forEach((solid, index) => {
    const dependencySet = new Set<number>();
    solid.inputs.forEach(input => {
      input.dependsOn.forEach(dependency => {
        if (dependency.solid.name) {
          dependencySet.add(indexMap.get(dependency.solid.name));
        }
      });
    });
    dependencySet.forEach(dependencyIndex => {
      adjacencyMatrix[index][dependencyIndex] = true;
    });
  });
  const matrix = new AdjacencyMatrix(adjacencyMatrix);
  memo.set(solids, matrix);
  return matrix;
}

export type SolidNameOrPath = { name: string } | { path: string[] };

export default class PipelineExplorer extends React.Component<
  IPipelineExplorerProps,
  IPipelineExplorerState
> {
  static fragments = {
    PipelineExplorerFragment: gql`
      fragment PipelineExplorerFragment on Pipeline {
        name
        description
        ...SidebarTabbedContainerPipelineFragment
      }

      ${SidebarTabbedContainer.fragments.SidebarTabbedContainerPipelineFragment}
    `,
    PipelineExplorerSolidHandleFragment: gql`
      fragment PipelineExplorerSolidHandleFragment on SolidHandle {
        handleID
        solid {
          name
          ...PipelineGraphSolidFragment
          ...SidebarTabbedContainerSolidFragment
        }
      }

      ${PipelineGraph.fragments.PipelineGraphSolidFragment}
      ${SidebarTabbedContainer.fragments.SidebarTabbedContainerSolidFragment}
    `
  };

  state = {
    filter: ""
  };

  memo = new WeakMap();

  handleAdjustPath = (fn: (solidNames: string[]) => void) => {
    const { history, pipeline, path } = this.props;
    const next = [...path];
    const retValue = fn(next);
    if (retValue !== undefined) {
      throw new Error(
        "handleAdjustPath function is expected to mutate the array"
      );
    }
    history.push(`/p/${pipeline.name}/explore/${next.join("/")}`);
  };

  // Note: this method handles relative solid paths, eg: {path: ['..', 'OtherSolid']}.
  // This is important because the DAG component tree doesn't always have access to a handleID,
  // and we sometimes want to be able to jump to a solid in the parent layer.
  //
  handleClickSolid = (arg: SolidNameOrPath) => {
    this.handleAdjustPath(solidNames => {
      if ("name" in arg) {
        solidNames[solidNames.length - 1] = arg.name;
      } else {
        if (arg.path[0] !== "..") {
          solidNames.length = 0;
        }
        if (arg.path[0] === ".." && solidNames[solidNames.length - 1] !== "") {
          solidNames.pop(); // remove the last path component indicating selection
        }
        while (arg.path[0] === "..") {
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
      this.handleAdjustPath(solidNames => {
        const last = "name" in arg ? arg.name : arg.path[arg.path.length - 1];
        solidNames[solidNames.length - 1] = last;
        solidNames.push("");
      });
    });
  };

  handleLeaveCompositeSolid = () => {
    this.handleAdjustPath(solidNames => {
      solidNames.pop();
    });
  };

  handleClickBackground = () => {
    this.handleClickSolid({ name: "" });
  };

  selectSolidsByFilter = (
    solids: PipelineExplorerSolidHandleFragment_solid[],
    filter: string,
    solidAdjacencyMatrix: AdjacencyMatrix
  ) => {
    let searchResults = new Array<PipelineExplorerSolidHandleFragment_solid>();
    searchResults = solids.filter(s => s.name.includes(filter));
    if (filter && filter.includes("+")) {
      let includeParents = false,
        includeChildren = false,
        invalidQuery = false,
        newFilterStart = 0,
        newFilterEnd = filter.length;

      for (let i = 0; i < filter.length; i++) {
        if (filter[i] === "+") {
          if (i !== 0 && i !== filter.length - 1) {
            // Can't have + inside the search term
            invalidQuery = true;
          }
          if (i === 0) {
            includeParents = true;
            newFilterStart = 1;
          }
          if (i === filter.length - 1) {
            includeChildren = true;
            newFilterEnd = -1;
          }
        }
      }
      if (!invalidQuery) {
        const solidFilter = filter.slice(newFilterStart, newFilterEnd);
        const candidateSolidIndexSet = new Set<number>();
        solids.forEach((solid, index) => {
          if (solidFilter && solid.name.includes(solidFilter)) {
            candidateSolidIndexSet.add(index);
            if (includeParents) {
              solidAdjacencyMatrix
                .fetchUpstream(index)
                .forEach(item => candidateSolidIndexSet.add(item));
            }
            if (includeChildren) {
              solidAdjacencyMatrix
                .fetchDownstream(index)
                .forEach(item => candidateSolidIndexSet.add(item));
            }
          }
        });
        searchResults.length = 0;
        candidateSolidIndexSet.forEach(index =>
          searchResults.push(solids[index])
        );
      }
    }
    return searchResults;
  };

  _layoutCacheKey: string | undefined;
  _layoutCache: IFullPipelineLayout | undefined;

  getLayout = (
    solids: PipelineExplorerSolidHandleFragment_solid[],
    parent: PipelineExplorerSolidHandleFragment_solid | undefined
  ) => {
    const key = solids.map(s => s.name).join("|");
    if (this._layoutCacheKey === key && this._layoutCache) {
      return this._layoutCache;
    }
    this._layoutCache = getDagrePipelineLayout(solids, parent);
    this._layoutCacheKey = key;
    return this._layoutCache;
  };

  public render() {
    const {
      pipeline,
      parentHandle,
      selectedHandle,
      selectedDefinitionInvocations,
      path
    } = this.props;
    const { filter } = this.state;

    const solids = this.props.handles.map(h => h.solid);

    const solidAdjacencyMatrix = createAdjacencyMatrix(solids, this.memo);

    const backgroundColor = parentHandle
      ? Colors.LIGHT_GRAY3
      : Colors.LIGHT_GRAY5;

    const backgroundTranslucent = Color(backgroundColor)
      .fade(0.6)
      .toString();

    return (
      <PipelinesContainer>
        <SplitPanelChildren
          identifier="explorer"
          leftInitialPercent={70}
          left={
            <>
              <PathOverlay style={{ background: backgroundTranslucent }}>
                <Link style={{ padding: 3 }} to={`/p/${pipeline.name}/explore`}>
                  <Icon icon="diagram-tree" />
                </Link>
                <Icon icon="chevron-right" />
                {path.slice(0, path.length - 1).map((name, idx) => (
                  <React.Fragment key={idx}>
                    <Link
                      style={{ padding: 3 }}
                      to={`/p/${pipeline.name}/explore/${path
                        .slice(0, idx + 1)
                        .join("/")}`}
                    >
                      {name}
                    </Link>
                    <Icon icon="chevron-right" />
                  </React.Fragment>
                ))}
                <SolidJumpBar
                  solids={solids}
                  selectedSolid={selectedHandle && selectedHandle.solid}
                  onItemSelect={solid =>
                    this.handleClickSolid({ name: solid.name })
                  }
                />
              </PathOverlay>
              <SearchOverlay style={{ background: backgroundTranslucent }}>
                <SolidSearchInput
                  type="text"
                  placeholder="Filter..."
                  name="filter"
                  value={filter}
                  onChange={e => this.setState({ filter: e.target.value })}
                />
              </SearchOverlay>
              <PipelineGraph
                pipelineName={pipeline.name}
                backgroundColor={backgroundColor}
                solids={solids}
                selectedHandleID={selectedHandle && selectedHandle.handleID}
                selectedSolid={selectedHandle && selectedHandle.solid}
                parentHandleID={parentHandle && parentHandle.handleID}
                parentSolid={parentHandle && parentHandle.solid}
                onClickSolid={this.handleClickSolid}
                onClickBackground={this.handleClickBackground}
                onEnterCompositeSolid={this.handleEnterCompositeSolid}
                onLeaveCompositeSolid={this.handleLeaveCompositeSolid}
                layout={this.getLayout(
                  solids,
                  parentHandle && parentHandle.solid
                )}
                highlightedSolids={this.selectSolidsByFilter(
                  solids,
                  this.state.filter,
                  solidAdjacencyMatrix
                )}
              />
            </>
          }
          right={
            <RightInfoPanel>
              <Route
                // eslint-disable-next-line react/no-children-prop
                children={({ location }: { location: any }) => (
                  <SidebarTabbedContainer
                    pipeline={pipeline}
                    solid={selectedHandle && selectedHandle.solid}
                    solidDefinitionInvocations={selectedDefinitionInvocations}
                    parentSolid={parentHandle && parentHandle.solid}
                    onEnterCompositeSolid={this.handleEnterCompositeSolid}
                    onClickSolid={this.handleClickSolid}
                    {...querystring.parse(location.search || "")}
                  />
                )}
              />
            </RightInfoPanel>
          }
        />
      </PipelinesContainer>
    );
  }
}

const PipelinesContainer = styled.div`
  flex: 1 1;
  display: flex;
  width: 100%;
  height: 100vh;
  top: 0;
  position: absolute;
  padding-top: 50px;
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

const SearchOverlay = styled.div`
  z-index: 2;
  padding: 7px 5px;
  display: inline-flex;
  align-items: stretch;
  position: absolute;
  right: 0;
`;

const PathOverlay = styled.div`
  z-index: 2;
  padding: 7px;
  padding-left: 10px;
  max-width: 80%;
  display: inline-flex;
  align-items: center;
  position: absolute;
  left: 0;
`;

const SolidSearchInput = styled.input`
  margin-left: 7px;
  padding: 5px 5px;
  font-size: 14px;
  border: 1px solid ${Colors.GRAY4};
`;
