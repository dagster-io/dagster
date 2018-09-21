import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { History } from "history";
import Config from "./Config";
import Solid from "./Solid";
import PipelineGraph from "./graph/PipelineGraph";
import { getDagrePipelineLayout } from "./graph/getFullSolidLayout";
import SolidListItem from "./SolidListItem";
import {
  PipelineFragment,
  PipelineFragment_solids
} from "./types/PipelineFragment";

interface IPipelineProps {
  pipeline: PipelineFragment;
  solid: PipelineFragment_solids | undefined;
  history: History;
}

export default class Pipeline extends React.Component<IPipelineProps, {}> {
  static fragments = {
    PipelineFragment: gql`
      fragment PipelineFragment on Pipeline {
        name
        description
        solids {
          ...SolidFragment
          ...SolidListItemFragment
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
      ${SolidListItem.fragments.SolidListItemFragment}
      ${Config.fragments.ConfigFragment}
    `
  };

  handleClickSolid = (solidName: string) => {
    const { history, pipeline } = this.props;
    history.push(`/${pipeline.name}/${solidName}`);
  };

  handleClickBackground = () => {
    const { history, pipeline } = this.props;
    history.push(`/${pipeline.name}`);
  };

  // renderContext() {
  //   return this.props.pipeline.contexts.map((context: any, i: number) => (
  //     <SpacedCard key={i}>
  //       <H5>
  //         <Code>{context.name}</Code>
  //       </H5>
  //       <DescriptionWrapper>
  //         <Description description={context.description} />
  //       </DescriptionWrapper>
  //       <Config config={context.config} />
  //     </SpacedCard>
  //   ));
  // }

  render() {
    return (
      <PipelineGraphWrapper key="graph">
        <PipelineGraph
          pipeline={this.props.pipeline}
          layout={getDagrePipelineLayout(this.props.pipeline)}
          selectedSolid={this.props.solid ? this.props.solid.name : undefined}
          onClickSolid={this.handleClickSolid}
          onClickBackground={this.handleClickBackground}
        />
      </PipelineGraphWrapper>
    );
  }
}

const Section = styled.div`
  margin-bottom: 30px;
`;

const PipelineGraphWrapper = styled(Section)`
  height: 700px;
  width: 100%;
  display: flex;
`;
