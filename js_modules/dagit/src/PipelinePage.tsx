import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Link } from "react-router-dom";
import { Route, match, Switch } from "react-router";
import { History } from "history";
import { Colors, NonIdealState, Alignment, Navbar } from "@blueprintjs/core";
import { PipelineJumpBar } from "./PipelineJumpComponents";
import PythonErrorInfo from "./PythonErrorInfo";
import PipelineExplorer from "./PipelineExplorer";
import PipelineExecutionRoot from "./execute/PipelineExecutionRoot";
import PipelineRunsRoot from "./runs/PipelineRunsRoot";
import PipelineRunRoot from "./runs/PipelineRunRoot";
import CustomAlertProvider from "./CustomAlertProvider";
import navBarImage from "./images/nav-logo.png";
import WebsocketStatus from "./WebsocketStatus";
import VersionLabel from "./VersionLabel";

import {
  PipelinePageFragment,
  PipelinePageFragment_PythonError,
  PipelinePageFragment_PipelineConnection_nodes,
  PipelinePageFragment_InvalidDefinitionError
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
    title: "Explore"
  },
  {
    slug: "execute",
    title: "Execute"
  },
  {
    slug: "runs",
    title: "Runs"
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
        ... on InvalidDefinitionError {
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

    let error:
      | PipelinePageFragment_PythonError
      | PipelinePageFragment_InvalidDefinitionError
      | null = null;
    let pipelines: Array<PipelinePageFragment_PipelineConnection_nodes> = [];

    if (pipelinesOrError.__typename === "PipelineConnection") {
      pipelines = pipelinesOrError.nodes;
    } else {
      error = pipelinesOrError;
    }

    const selectedTab = TABS.find(t => t.slug === match.params.tab) || TABS[0];
    const selectedPipeline = pipelines.find(
      p => p.name === match.params.pipeline
    );

    let body;

    if (error) {
      body = <PythonErrorInfo error={error} centered={true} />;
    } else if (selectedPipeline && selectedTab) {
      body = (
        <Switch>
          <Route
            path="/:pipelineName/execute"
            component={PipelineExecutionRoot}
          />
          <Route
            path="/:pipelineName/runs/:runId"
            component={PipelineRunRoot}
          />
          <Route
            exact={true}
            path="/:pipelineName/runs"
            component={PipelineRunsRoot}
          />
          <Route
            path="/:pipelineName/:solid"
            render={({ match }) => (
              <PipelineExplorer
                history={history}
                pipeline={selectedPipeline}
                solid={selectedPipeline.solids.find(
                  s => s.name === match.params.solid
                )}
              />
            )}
          />
        </Switch>
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
      <>
        <Navbar>
          <Navbar.Group align={Alignment.LEFT}>
            <Navbar.Heading onClick={() => history.push("/")}>
              <img src={navBarImage} style={{ height: 34 }} />
            </Navbar.Heading>
            <Navbar.Divider />
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
          </Navbar.Group>
          <Navbar.Group align={Alignment.RIGHT}>
            <WebsocketStatus />
            <VersionLabel />
          </Navbar.Group>
        </Navbar>
        {body}
        <CustomAlertProvider />
      </>
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
