import * as React from "react";
import gql from "graphql-tag";
import { History } from "history";
import { NonIdealState } from "@blueprintjs/core";
import Page from "./Page";
import PipelineExplorer from "./PipelineExplorer";
import PipelineJumpBar from "./PipelineJumpBar";
import PythonErrorInfo from "./PythonErrorInfo";
import {
  PipelinePageFragment,
  PipelinePageFragment_Pipeline
} from "./types/PipelinePageFragment";

interface IPipelinePageProps {
  pipelinesOrErrors: Array<PipelinePageFragment>;
  selectedPipelineName: string | null;
  selectedSolidName: string | null;
  history: History;
}

export default class PipelinePage extends React.Component<
  IPipelinePageProps,
  {}
> {
  static fragments = {
    PipelinePageFragment: gql`
      fragment PipelinePageFragment on PipelineOrError {
        __typename
        ... on Error {
          message
          stack
        }
        ... on Pipeline {
          ...PipelineFragment
          ...PipelineJumpBarFragment
        }
      }

      ${PipelineExplorer.fragments.PipelineExplorerFragment}
      ${PipelineJumpBar.fragments.PipelineJumpBarFragment}
    `
  };

  render() {
    let body;
    const first = this.props.pipelinesOrErrors[0];
    const pipelines: Array<PipelinePageFragment_Pipeline> = [];
    for (const pipelineOrError of this.props.pipelinesOrErrors) {
      if (pipelineOrError.__typename === "PythonError") {
        body = <PythonErrorInfo error={pipelineOrError} />;
      } else {
        pipelines.push(pipelineOrError);
      }
    }

    const selectedPipeline = pipelines.find(
      p => p.name === this.props.selectedPipelineName
    );

    if (!selectedPipeline) {
      body = (
        <NonIdealState
          title="No pipeline selected"
          description="Select a pipeline in the navbar"
        />
      );
    }

    const selectedSolid =
      selectedPipeline &&
      selectedPipeline.solids.find(
        s => s.name === this.props.selectedSolidName
      );

    if (!body && selectedPipeline) {
      body = (
        <PipelineExplorer
          pipeline={selectedPipeline}
          solid={selectedSolid}
          history={this.props.history}
        />
      );
    }

    return (
      <Page
        history={this.props.history}
        navbarContents={
          <PipelineJumpBar
            selectedPipeline={selectedPipeline}
            selectedSolid={selectedSolid}
            pipelines={pipelines}
            history={this.props.history}
          />
        }
      >
        {body}
      </Page>
    );
  }
}
