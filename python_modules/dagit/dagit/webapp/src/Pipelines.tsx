import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { History } from "history";
import { NonIdealState, Colors } from "@blueprintjs/core";
import Pipeline from "./Pipeline";
import { PipelinesFragment } from "./types/PipelinesFragment";
import { PipelineFragment } from "./types/PipelineFragment";
import { Switch, Route } from "react-router";
import { Link } from "react-router-dom";
import Description from "./Description";
import SolidListItem from "./SolidListItem";

interface IPipelinesProps {
  history: History;
  pipelines: Array<PipelinesFragment>;
  selectedPipeline: string;
  selectedSolid: string;
}

export default class Pipelines extends React.Component<IPipelinesProps, {}> {
  static fragments = {
    PipelinesFragment: gql`
      fragment PipelinesFragment on Pipeline {
        ...PipelineFragment
      }

      ${Pipeline.fragments.PipelineFragment}
    `
  };

  public render() {
    const pipeline = this.props.pipelines.find(
      ({ name }) => name === this.props.selectedPipeline
    );
    const solid =
      pipeline &&
      pipeline.solids.find(({ name }) => name === this.props.selectedSolid);

    if (!pipeline) {
      return (
        <NonIdealState
          title="No pipeline selected"
          description="Select a pipeline in the sidebar on the left"
        />
      );
    }
    return (
      <PipelinesContainer>
        <PipelinePanel>
          <Pipeline
            pipeline={pipeline}
            solid={solid}
            history={this.props.history}
          />
        </PipelinePanel>
        <RightInfoPanel>
          {solid ? (
            <SolidListItem
              pipelineName={pipeline.name}
              solid={solid}
              key={solid.name}
            />
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
`;
const PipelinePanel = styled.div`
  width: 70vw;
`;
const RightInfoPanel = styled.div`
  width: 30vw;
  background: ${Colors.WHITE};
`;

const DescriptionWrapper = styled.div`
  max-width: 500px;
  padding: 20px;
`;
