import * as React from "react";

import { Colors, Icon } from "@blueprintjs/core";

import { Link } from "react-router-dom";
import { PipelineJumpBar } from "./PipelineJumpComponents";
import { Route } from "react-router";
import { LeftNavPipelinesFragment } from "./types/LeftNavPipelinesFragment";
import ProcessStatus from "./ProcessStatus";
import WebsocketStatus from "./WebsocketStatus";
import gql from "graphql-tag";
import navBarImage from "./images/nav-logo-icon.png";
import styled from "styled-components/macro";

export const LeftNav = ({
  pipelines
}: {
  pipelines: LeftNavPipelinesFragment[];
}) => (
  <Route
    path="/:scope?/:scopeArg?/:tab?"
    render={({ match: { params }, history }) => {
      const { scope, scopeArg, tab } = params;

      const selectedTab = scope === "p" ? tab : scope;
      const selectedPipelineName =
        scope === "p" ? scopeArg : pipelines[0] ? pipelines[0].name : "null";

      return (
        <Tabs>
          <LogoContainer onClick={() => history.push("/")}>
            <img src={navBarImage} style={{ height: 40 }} alt="logo" />
            <WebsocketStatus
              style={{ position: "absolute", top: 28, right: -3 }}
            />
          </LogoContainer>

          <Tab
            to={`/p/${selectedPipelineName}/explore`}
            className={selectedTab === "explore" ? "active" : ""}
          >
            <Icon icon="diagram-tree" iconSize={30} />
            <TabLabel>Pipelines</TabLabel>
          </Tab>
          <Tab
            to={`/solids`}
            className={selectedTab === "solids" ? "active" : ""}
          >
            <Icon icon="git-commit" iconSize={30} />
            <TabLabel>Solids</TabLabel>
          </Tab>
          <Tab to={`/runs`} className={selectedTab === "runs" ? "active" : ""}>
            <Icon icon="history" iconSize={30} />
            <TabLabel>Runs</TabLabel>
          </Tab>
          <Tab
            to={`/p/${selectedPipelineName}/execute`}
            className={selectedTab === "execute" ? "active" : ""}
          >
            <Icon icon="manually-entered-data" iconSize={30} />
            <TabLabel>Playground</TabLabel>
          </Tab>
          <Tab
            to={`/scheduler`}
            className={selectedTab === "scheduler" ? "active" : ""}
          >
            <Icon icon="calendar" iconSize={30} />
            <TabLabel>Schedule</TabLabel>
          </Tab>
          <div style={{ flex: 1 }} />
          <ProcessStatus />
        </Tabs>
      );
    }}
  />
);

LeftNav.fragments = {
  LeftNavPipelinesFragment: gql`
    fragment LeftNavPipelinesFragment on Pipeline {
      ...PipelineJumpBarFragment
    }
    ${PipelineJumpBar.fragments.PipelineJumpBarFragment}
  `
};

const Tabs = styled.div`
  width: 74px;
  height: 100%;
  display: flex;
  flex-shrink: 0;
  flex-direction: column;
  justify-content: center;
  background: ${Colors.DARK_GRAY2};
  border-right: 1px solid ${Colors.DARK_GRAY5};
  padding: 14px 0;
`;

const Tab = styled(Link)`
  color: ${Colors.LIGHT_GRAY1};
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 4px 0;
  margin: 8px 0;
  align-items: center;
  outline: 0;
  &:hover {
    color: ${Colors.WHITE};
    text-decoration: none;
  }
  &.active {
    color: ${Colors.WHITE};
    border-left: 4px solid ${Colors.COBALT3};
  }
`;

const TabLabel = styled.div`
  font-size: 11px;
  margin-top: 6px;
  text-decoration: none;
  white-space: nowrap;
  text-decoration: none;
`;

const LogoContainer = styled.div`
  margin: auto;
  margin-bottom: 10px;
  position: relative;
`;
