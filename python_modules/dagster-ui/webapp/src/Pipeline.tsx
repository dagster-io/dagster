import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Card, H2, H5, Text, Code } from "@blueprintjs/core";
import SpacedCard from "./SpacedCard";
import Argumented from "./Argumented";
import Solid from "./Solid";
import PipelineGraph from "./graph/PipelineGraph";
import { PipelineFragment } from "./types/PipelineFragment";

interface IPipelineProps {
  pipeline: PipelineFragment;
}

interface IPipelineState {
  selectedNode: string;
}

export default class Pipeline extends React.Component<IPipelineProps, {}> {
  static fragments = {
    PipelineFragment: gql`
      fragment PipelineFragment on Pipeline {
        name
        description
        solids {
          ...SolidFragment
        }
        context {
          ...PipelineContextFragment
        }
        ...PipelineGraphFragment
      }

      ${Solid.fragments.SolidFragment}
      ${Argumented.fragments.PipelineContextFragment}
      ${PipelineGraph.fragments.PipelineGraphFragment}
    `
  };

  renderContext() {
    return this.props.pipeline.context.map((context: any, i: number) => (
      <Argumented key={i} item={context} />
    ));
  }

  renderSolids() {
    return this.props.pipeline.solids.map((solid: any, i: number) => (
      <Solid key={i} solid={solid} />
    ));
  }

  public render() {
    return (
      <PipelineCard>
        <H2>
          <Code>{this.props.pipeline.name}</Code>
        </H2>
        <PipelineGraphWrapper>
          <PipelineGraph pipeline={this.props.pipeline} />
        </PipelineGraphWrapper>
        <Text>{this.props.pipeline.description}</Text>
        <SpacedCard elevation={1}>
          <H5>Context</H5>
          {this.renderContext()}
        </SpacedCard>
        <SpacedCard elevation={1}>
          <H5>Solids</H5>
          <SolidLayout>{this.renderSolids()}</SolidLayout>
        </SpacedCard>
      </PipelineCard>
    );
  }
}

const PipelineGraphWrapper = styled(Card)`
  height: 500px;
  width: 100%;
  display: flex;
`;

const PipelineCard = styled(Card)`
  flex: 1 1;
`;

const SolidLayout = styled.div`
  flex: 1 1;
  display: flex;
  flex-direction: row;
`;
