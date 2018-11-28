import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Link } from "react-router-dom";
import { Route, match } from "react-router";
import { History } from "history";
import { Colors, NonIdealState, Navbar } from "@blueprintjs/core";
import Page from "./Page";
import { PipelineJumpBar } from "./PipelineJumpComponents";
import PythonErrorInfo from "./PythonErrorInfo";
import PipelineExplorer from "./PipelineExplorer";
import PipelineExecution from "./PipelineExecution";
import {
  PipelinePageFragment,
  PipelinePageFragment_Pipeline,
  PipelinePageFragment_PythonError,
  PipelinePageFragment_PipelineNotFoundError,
} from "./types/PipelinePageFragment";

export type IPipelinePageMatch = match<{
  pipeline: string | null;
  tab: string | null;
}>;

interface IPipelinePageProps {
  history: History;
  match: IPipelinePageMatch;
  pipelinesOrErrors: Array<PipelinePageFragment>;
}

interface IPipelinePageTabProps extends IPipelinePageProps {
  pipeline: PipelinePageFragment_Pipeline;
}

const TABS = [
  {
    slug: "explore",
    title: "Explore",
    render: (props: IPipelinePageTabProps) => (
      <Route
        path={`${props.match.url}/:solid?`}
        render={({ match }: { match: match<{ solid: string | null }> }) => (
          <PipelineExplorer
            history={props.history}
            pipeline={props.pipeline}
            solid={props.pipeline.solids.find(
              s => s.name === match.params.solid
            )}
          />
        )}
      />
    )
  },
  {
    slug: "execute",
    title: "Execute",
    render: (props: IPipelinePageTabProps) => (
      <PipelineExecution pipeline={props.pipeline} />
    )
  }
];

export default class PipelinePage extends React.Component<IPipelinePageProps> {
  static fragments = {
    PipelinePageFragment: gql`
      fragment PipelinePageFragment on PipelineOrError {
        __typename
        ... on PythonError {
          message
          stack
        }
        ... on PipelineNotFoundError {
          message
          stack
        }
        ... on Pipeline {
          ...PipelineExecutionFragment
          ...PipelineExplorerFragment
          ...PipelineJumpBarFragment
          solids {
            ...PipelineExplorerSolidFragment
          }
        }
      }

      ${PipelineExecution.fragments.PipelineExecutionFragment}
      ${PipelineExplorer.fragments.PipelineExplorerFragment}
      ${PipelineExplorer.fragments.PipelineExplorerSolidFragment}
      ${PipelineJumpBar.fragments.PipelineJumpBarFragment}
    `
  };

  render() {
    const { history, match, pipelinesOrErrors } = this.props;

    let error: PipelinePageFragment_PipelineNotFoundError | PipelinePageFragment_PythonError | null = null;
    const pipelines: Array<PipelinePageFragment_Pipeline> = [];

    for (const pipelineOrError of pipelinesOrErrors) {
      if (pipelineOrError.__typename === "PythonError" || pipelineOrError.__typename == "PipelineNotFoundError") {
        error = pipelineOrError;
      } else {
        pipelines.push(pipelineOrError);
      }
    }

    const selectedTab = TABS.find(t => t.slug === match.params.tab) || TABS[0];
    const selectedPipeline = pipelines.find(
      p => p.name === match.params.pipeline
    );

    let body;

    if (error) {
      body = <PythonErrorInfo error={error} />;
    } else if (selectedPipeline && selectedTab) {
      body = selectedTab.render(
        Object.assign({ pipeline: selectedPipeline }, this.props)
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
          <PipelineNavbar>
            <PipelineJumpBar
              pipelines={pipelines}
              selectedPipeline={selectedPipeline}
              onItemSelect={pipeline => {
                history.push(`/${pipeline.name}/${match.params.tab}`);
              }}
            />
            {selectedPipeline && <Navbar.Divider />}
            {selectedPipeline && (
              <Tabs>
                {TABS.map(({ slug, title }) => (
                  <Tab
                    key={slug}
                    to={`/${selectedPipeline.name}/${slug}`}
                    active={match.params.tab === slug}
                  >
                    {title}
                  </Tab>
                ))}
              </Tabs>
            )}
          </PipelineNavbar>
        }
      >
        {body}
      </Page>
    );
  }
}

const PipelineNavbar = styled.div`
  display: flex;
  align-items: center;
`;

const Tabs = styled.div`
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
`;

const Tab = styled(Link)<{ active: boolean }>`
  color: ${p => (p.active ? Colors.COBALT3 : Colors.GRAY2)}
  border-top: 3px solid transparent;
  border-bottom: 3px solid ${p => (p.active ? Colors.COBALT3 : "transparent")}
  text-decoration: none;
  white-space: nowrap;
  min-width: 40px;
  padding: 0 10px;
  display: flex;
  height: 50px;
  align-items: center;
  outline: 0;
`;
