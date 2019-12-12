import * as React from "react";
import gql from "graphql-tag";
import Color from "color";
import styled from "styled-components/macro";
import { History } from "history";
import { Icon, Colors, InputGroup } from "@blueprintjs/core";
import { Route } from "react-router";
import { Link } from "react-router-dom";
import * as querystring from "query-string";

import { PipelineExplorerFragment } from "./types/PipelineExplorerFragment";
import { PipelineGraphContainer } from "./graph/PipelineGraphContainer";
import PipelineGraph from "./graph/PipelineGraph";
import { SplitPanelChildren } from "./SplitPanelChildren";
import SidebarTabbedContainer from "./SidebarTabbedContainer";
import { PipelineExplorerSolidHandleFragment } from "./types/PipelineExplorerSolidHandleFragment";
import { PipelineExplorerParentSolidHandleFragment } from "./types/PipelineExplorerParentSolidHandleFragment";
import { SolidJumpBar } from "./PipelineJumpComponents";
import { SolidQueryInput } from "./SolidQueryInput";
import { filterSolidsByQuery } from "./SolidQueryImpl";

interface PipelineExplorerProps {
  history: History;
  path: string[];
  pipeline: PipelineExplorerFragment;
  handles: PipelineExplorerSolidHandleFragment[];
  selectedHandle?: PipelineExplorerSolidHandleFragment;
  parentHandle?: PipelineExplorerParentSolidHandleFragment;
  getInvocations?: (definitionName: string) => { handleID: string }[];
}

interface PipelineExplorerState {
  visibleSolidsQuery: string;
  highlighted: string;
}

export type SolidNameOrPath = { name: string } | { path: string[] };

export default class PipelineExplorer extends React.Component<
  PipelineExplorerProps,
  PipelineExplorerState
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
        }
      }
      ${PipelineGraph.fragments.PipelineGraphSolidFragment}
    `,
    PipelineExplorerParentSolidHandleFragment: gql`
      fragment PipelineExplorerParentSolidHandleFragment on SolidHandle {
        handleID
        solid {
          name
          ...PipelineGraphParentSolidFragment
        }
      }
      ${PipelineGraph.fragments.PipelineGraphParentSolidFragment}
    `
  };

  state = {
    visibleSolidsQuery: "",
    highlighted: ""
  };

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

  public render() {
    const { pipeline, parentHandle, path } = this.props;
    const { visibleSolidsQuery, highlighted } = this.state;

    const solids = this.props.handles.map(h => h.solid);
    const solidsQueryEnabled = !parentHandle;
    const queryResultSolids = solidsQueryEnabled
      ? filterSolidsByQuery(solids, visibleSolidsQuery)
      : { all: solids, focus: [] };

    const highlightedSolids = queryResultSolids.all.filter(s =>
      s.name.includes(highlighted)
    );

    let selectedHandle = this.props.selectedHandle;
    if (
      selectedHandle &&
      !queryResultSolids.all.some(s => s.name === selectedHandle!.solid.name)
    ) {
      selectedHandle = undefined;
    }

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
                  solids={queryResultSolids.all}
                  selectedSolid={selectedHandle && selectedHandle.solid}
                  onItemSelect={solid =>
                    this.handleClickSolid({ name: solid.name })
                  }
                />
              </PathOverlay>
              {solidsQueryEnabled && (
                <SolidQueryInput
                  solids={solids}
                  value={visibleSolidsQuery}
                  onChange={q => this.setState({ visibleSolidsQuery: q })}
                />
              )}
              <SearchOverlay style={{ background: backgroundTranslucent }}>
                <SolidHighlightInput
                  type="text"
                  name="highlighted"
                  leftIcon="search"
                  value={highlighted}
                  placeholder="Highlight..."
                  onChange={(e: React.ChangeEvent<any>) =>
                    this.setState({ highlighted: e.target.value })
                  }
                />
              </SearchOverlay>
              {queryResultSolids.all.length === 0 &&
                !visibleSolidsQuery.length && <LargeDAGNotice />}
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
          right={
            <RightInfoPanel>
              <Route
                // eslint-disable-next-line react/no-children-prop
                children={({ location }: { location: any }) => (
                  <SidebarTabbedContainer
                    pipeline={pipeline}
                    solidHandleID={selectedHandle && selectedHandle.handleID}
                    parentSolidHandleID={parentHandle && parentHandle.handleID}
                    getInvocations={this.props.getInvocations}
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

const SolidHighlightInput = styled(InputGroup)`
  margin-left: 7px;
  font-size: 14px;
  width: 220px;
`;

const LargeDAGNotice = () => (
  <LargeDAGContainer>
    <LargeDAGInstructionBox>
      <p>
        This is a large DAG that may be difficult to visualize. Type{" "}
        <code>*</code> in the subset box above to render the entire thing, or
        type a solid name and use:
      </p>
      <ul style={{ marginBottom: 0 }}>
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
