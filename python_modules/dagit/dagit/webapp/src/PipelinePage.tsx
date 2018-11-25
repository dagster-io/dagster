import * as React from "react";
import gql from "graphql-tag";
import { History } from "history";
import { NonIdealState } from "@blueprintjs/core";
import Page from "./Page";
import PipelineExplorer from "./PipelineExplorer";
import { PipelineJumpBar } from "./PipelineJumpComponents";
import PythonErrorInfo from "./PythonErrorInfo";
import {
  PipelinePageFragment,
  PipelinePageFragment_Pipeline,
  PipelinePageFragment_PythonError
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
          ...PipelineExplorerFragment
          ...PipelineJumpBarFragment
          solids {
            ...PipelineExplorerSolidFragment
          }
        }
      }

      ${PipelineExplorer.fragments.PipelineExplorerFragment}
      ${PipelineExplorer.fragments.PipelineExplorerSolidFragment}
      ${PipelineJumpBar.fragments.PipelineJumpBarFragment}
    `
  };

  render() {
    let error: PipelinePageFragment_PythonError | null = null;
    const pipelines: Array<PipelinePageFragment_Pipeline> = [];

    for (const pipelineOrError of this.props.pipelinesOrErrors) {
      if (pipelineOrError.__typename === "PythonError") {
        error = pipelineOrError;
      } else {
        pipelines.push(pipelineOrError);
      }
    }

    const selectedPipeline = pipelines.find(
      p => p.name === this.props.selectedPipelineName
    );

    const selectedSolid =
      selectedPipeline &&
      selectedPipeline.solids.find(
        s => s.name === this.props.selectedSolidName
      );

    let body;

    if (error) {
      body = <PythonErrorInfo error={error} />;
    } else if (selectedPipeline) {
      body = (
        <PipelineExplorer
          pipeline={selectedPipeline}
          solid={selectedSolid}
          history={this.props.history}
        />
      );
    } else {
      body = (
        <NonIdealState
          title="No pipeline selected"
          description="Select a pipeline in the navbar"
        />
      );
    }

    return (
      <Page
        history={this.props.history}
        navbarContents={
          <PipelineJumpBar
            pipelines={pipelines}
            selectedPipeline={selectedPipeline}
            onItemSelect={pipeline => {
              this.props.history.push(`/${pipeline.name}`);
            }}
          />
        }
      >
        {body}
      </Page>
    );
  }
}
