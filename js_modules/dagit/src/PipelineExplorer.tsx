import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { History } from "history";
import { Colors } from "@blueprintjs/core";
import { Route } from "react-router";
import { parse as parseQueryString } from "query-string";
import { PipelineExplorerFragment } from "./types/PipelineExplorerFragment";
import { PipelineExplorerSolidFragment } from "./types/PipelineExplorerSolidFragment";
import PipelineGraph from "./graph/PipelineGraph";
import { getDagrePipelineLayout } from "./graph/getFullSolidLayout";
import { PanelDivider } from "./PanelDivider";
import SidebarTabbedContainer from "./SidebarTabbedContainer";
import { SolidJumpBar } from "./PipelineJumpComponents";

interface IPipelineExplorerProps {
  history: History;
  pipeline: PipelineExplorerFragment;
  solid: PipelineExplorerSolidFragment | undefined;
}

interface IPipelineExplorerState {
  filter: string;
  graphVW: number;
}
export default class PipelineExplorer extends React.Component<
  IPipelineExplorerProps,
  IPipelineExplorerState
> {
  static fragments = {
    PipelineExplorerFragment: gql`
      fragment PipelineExplorerFragment on Pipeline {
        name
        description
        contexts {
          name
          description
        }
        ...PipelineGraphFragment
        ...SidebarTabbedContainerPipelineFragment
      }

      ${PipelineGraph.fragments.PipelineGraphFragment}
      ${SidebarTabbedContainer.fragments.SidebarTabbedContainerPipelineFragment}
    `,
    PipelineExplorerSolidFragment: gql`
      fragment PipelineExplorerSolidFragment on Solid {
        name
        ...PipelineGraphSolidFragment
        ...SidebarTabbedContainerSolidFragment
      }

      ${PipelineGraph.fragments.PipelineGraphSolidFragment}
      ${SidebarTabbedContainer.fragments.SidebarTabbedContainerSolidFragment}
    `
  };

  constructor(props: IPipelineExplorerProps) {
    super(props);
    this.state = {
      filter: "",
      graphVW: 70
    };
  }

  handleClickSolid = (solidName: string) => {
    const { history, pipeline } = this.props;
    history.push(`/${pipeline.name}/explore/${solidName}`);
  };

  handleClickBackground = () => {
    const { history, pipeline } = this.props;
    history.push(`/${pipeline.name}/explore`);
  };

  public render() {
    const { pipeline, solid } = this.props;
    const { filter, graphVW } = this.state;

    return (
      <PipelinesContainer>
        <PipelinePanel key="graph" style={{ width: `${graphVW}vw` }}>
          <SearchOverlay>
            <SolidJumpBar
              solids={pipeline.solids}
              selectedSolid={solid}
              onItemSelect={solid => this.handleClickSolid(solid.name)}
            />
            <SolidSearchInput
              type="text"
              placeholder="Filter..."
              value={filter}
              onChange={e => this.setState({ filter: e.target.value })}
            />
          </SearchOverlay>
          <PipelineGraph
            pipeline={pipeline}
            onClickSolid={this.handleClickSolid}
            onClickBackground={this.handleClickBackground}
            layout={getDagrePipelineLayout(pipeline)}
            selectedSolid={solid}
            highlightedSolids={pipeline.solids.filter(
              s => filter && s.name.includes(filter)
            )}
          />
        </PipelinePanel>
        <PanelDivider
          axis="horizontal"
          onMove={(vw: number) =>
            this.setState({
              graphVW: vw
            })
          }
        />
        <RightInfoPanel style={{ width: `${100 - graphVW}vw` }}>
          <Route
            children={({ location }: { location: any }) => (
              <SidebarTabbedContainer
                pipeline={pipeline}
                solid={solid}
                {...parseQueryString(location.search || "")}
              />
            )}
          />
        </RightInfoPanel>
      </PipelinesContainer>
    );
  }
}

function getConfigStorageKey(pipeline: PipelineExplorerFragment) {
  return `dagit.pipelineConfigStorage.${pipeline.name}`;
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

const PipelinePanel = styled.div`
  height: 100%;
  position: relative;
`;

const RightInfoPanel = styled.div`
  height: 100%;
  overflow-y: scroll;
  background: ${Colors.WHITE};
`;

const SearchOverlay = styled.div`
  background: rgba(0, 0, 0, 0.2);
  z-index: 2;
  padding: 7px;
  display: inline-flex;
  align-items: stretch;
  position: absolute;
  right: 0;
`;

const SolidSearchInput = styled.input`
  margin-left: 7px;
  padding: 5px 5px;
  font-size: 14px;
  border: 1px solid ${Colors.GRAY4};
`;
