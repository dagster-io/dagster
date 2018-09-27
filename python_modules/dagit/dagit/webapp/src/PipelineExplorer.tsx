import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { History } from "history";
import { Colors } from "@blueprintjs/core";

import {
  PipelinesFragment,
  PipelinesFragment_solids
} from "./types/PipelinesFragment";
import Description from "./Description";
import Config from "./Config";
import Solid from "./Solid";
import PipelineGraph from "./graph/PipelineGraph";
import { getDagrePipelineLayout } from "./graph/getFullSolidLayout";
import { PanelDivider } from "./PanelDivider";

interface IPipelineExplorerProps {
  history: History;
  pipeline: PipelinesFragment;
  solid: PipelinesFragment_solids | undefined;
}

interface IPipelineExplorerState {
  search: string;
  graphVW: number;
}

export default class PipelineExplorer extends React.Component<
  IPipelineExplorerProps,
  IPipelineExplorerState
> {
  static fragments = {
    PipelineFragment: gql`
      fragment PipelineFragment on Pipeline {
        name
        description
        solids {
          ...SolidFragment
        }
        contexts {
          name
          description
          config {
            ...ConfigFragment
          }
        }
        ...PipelineGraphFragment
      }

      ${Solid.fragments.SolidFragment}
      ${PipelineGraph.fragments.PipelineGraphFragment}
      ${Config.fragments.ConfigFragment}
    `
  };

  state = {
    search: "",
    graphVW: 70
  };

  handleClickSolid = (solidName: string) => {
    const { history, pipeline } = this.props;
    history.push(`/${pipeline.name}/${solidName}`);
  };

  handleClickBackground = () => {
    const { history, pipeline } = this.props;
    history.push(`/${pipeline.name}`);
  };

  public render() {
    const { pipeline, solid } = this.props;
    const { search, graphVW } = this.state;

    return (
      <PipelinesContainer>
        <PipelinePanel key="graph" style={{ width: `${graphVW}vw` }}>
          <SearchOverlay>
            <input
              type="text"
              placeholder="Search..."
              value={search}
              onChange={e => this.setState({ search: e.target.value })}
            />
          </SearchOverlay>
          <PipelineGraph
            pipeline={pipeline}
            layout={getDagrePipelineLayout(pipeline)}
            selectedSolid={solid}
            highlightedSolids={pipeline.solids.filter(
              s => search && s.name.includes(search)
            )}
            onClickSolid={this.handleClickSolid}
            onClickBackground={this.handleClickBackground}
          />
        </PipelinePanel>
        <PanelDivider onMove={(vw: number) => this.setState({ graphVW: vw })} />
        <RightInfoPanel style={{ width: `${100 - graphVW}vw` }}>
          {solid ? (
            <Solid solid={solid} key={solid.name} />
          ) : (
            <DescriptionWrapper>
              <h2>{pipeline.name}</h2>
              <Description description={pipeline ? pipeline.description : ""} />
            </DescriptionWrapper>
          )}
        </RightInfoPanel>
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

const PipelinePanel = styled.div`
  height: 100%;
  position: relative;
`;

const RightInfoPanel = styled.div`
  height: 100%;
  overflow-y: scroll;
  background: ${Colors.WHITE};
`;

const DescriptionWrapper = styled.div`
  max-width: 500px;
  padding: 20px;
`;

const SearchOverlay = styled.div`
  background: rgba(0, 0, 0, 0.2);
  z-index: 2;
  padding: 7px;
  display: inline-block;
  width: 150px;
  position: absolute;
  right: 0;
`;
