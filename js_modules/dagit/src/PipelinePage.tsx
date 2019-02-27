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
import PipelineExecutionRoot from "./execution/PipelineExecutionRoot";

import {
  PipelinePageFragment,
  PipelinePageFragment_PythonError,
  PipelinePageFragment_PipelineConnection_nodes
} from "./types/PipelinePageFragment";

export type IPipelinePageMatch = match<{
  pipeline: string | undefined;
  tab: string | undefined;
}>;

interface IPipelinePageProps {
  history: History;
  match: IPipelinePageMatch;
  pipelinesOrError: PipelinePageFragment;
}

interface IPipelinePageTabProps extends IPipelinePageProps {
  pipeline: PipelinePageFragment_PipelineConnection_nodes;
}

const TABS = [
  {
    slug: "explore",
    title: "Explore",
    render: (props: IPipelinePageTabProps) => (
      <Route
        path={`${props.match.url}/:solid?`}
        render={({
          match
        }: {
          match: match<{ solid: string | undefined }>;
        }) => (
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
      <PipelineExecutionRoot pipeline={props.pipeline.name} />
    )
  }
];

export default class PipelinePage extends React.Component<IPipelinePageProps> {
  static fragments = {
    PipelinePageFragment: gql`
      fragment PipelinePageFragment on PipelinesOrError {
        __typename
        ... on PythonError {
          message
          stack
        }
        ... on PipelineConnection {
          nodes {
            ...PipelineExplorerFragment
            ...PipelineJumpBarFragment
            solids {
              ...PipelineExplorerSolidFragment
            }
          }
        }
      }

      ${PipelineExplorer.fragments.PipelineExplorerFragment}
      ${PipelineExplorer.fragments.PipelineExplorerSolidFragment}
      ${PipelineJumpBar.fragments.PipelineJumpBarFragment}
    `
  };

  render() {
    const { history, match, pipelinesOrError } = this.props;

    let error: PipelinePageFragment_PythonError | null = null;
    let pipelines: Array<PipelinePageFragment_PipelineConnection_nodes> = [];

    if (pipelinesOrError.__typename === "PythonError") {
      error = pipelinesOrError;
    } else {
      pipelines = pipelinesOrError.nodes;
    }

    const selectedTab = TABS.find(t => t.slug === match.params.tab) || TABS[0];
    const selectedPipeline = pipelines.find(
      p => p.name === match.params.pipeline
    );

    let body;

    if (error) {
      body = <PythonErrorInfo error={error} centered={true} />;
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
                history.push(`/${pipeline.name}/${selectedTab.slug}`);
              }}
            />
            {selectedPipeline && <Navbar.Divider />}
            {selectedPipeline && (
              <Tabs>
                {TABS.map(({ slug, title }) => (
                  <Tab
                    key={slug}
                    to={`/${selectedPipeline.name}/${slug}`}
                    className={selectedTab.slug === slug ? "active" : ""}
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

const Tab = styled(Link)`
  color: ${Colors.GRAY2}
  border-top: 3px solid transparent;
  border-bottom: 3px solid transparent;
  text-decoration: none;
  white-space: nowrap;
  min-width: 40px;
  padding: 0 10px;
  display: flex;
  height: 50px;
  align-items: center;
  outline: 0;
  &.active {
    color: ${Colors.COBALT3};
    border-bottom: 3px solid ${Colors.COBALT3};
  }
`;
