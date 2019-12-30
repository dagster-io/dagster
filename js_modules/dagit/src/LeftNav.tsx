import * as React from "react";

import { Colors, Icon } from "@blueprintjs/core";

import { Link } from "react-router-dom";
import { Route } from "react-router";
import ProcessStatus from "./ProcessStatus";
import WebsocketStatus from "./WebsocketStatus";
import navBarImage from "./images/nav-logo-icon.png";
import styled from "styled-components/macro";
import { PipelineNamesContext } from "./PipelineNamesContext";

const LAST_PIPELINE = "last-pipeline";

export const LeftNav = () => {
  const pipelineNames = React.useContext(PipelineNamesContext);

  return (
    <Route
      path="/:tab?/:pipelineSelector?"
      render={({ match: { params }, history }) => {
        const { tab } = params;

        if (tab === "pipeline") {
          window.localStorage.setItem(LAST_PIPELINE, params.pipelineSelector);
        }

        let pipelineSelector = window.localStorage.getItem(LAST_PIPELINE);
        if (!pipelineSelector) {
          pipelineSelector = `${pipelineNames[0]}:`;
        }
        if (
          pipelineNames &&
          !pipelineNames.includes(pipelineSelector.split(":")[0])
        ) {
          pipelineSelector = `${pipelineNames[0]}:`;
        }

        return (
          <Tabs>
            <LogoContainer onClick={() => history.push("/")}>
              <img src={navBarImage} style={{ height: 40 }} alt="logo" />
              <WebsocketStatus
                style={{ position: "absolute", top: 28, right: -3 }}
              />
            </LogoContainer>

            <Tab
              to={`/pipeline/${pipelineSelector}/`}
              className={tab === "pipeline" ? "active" : ""}
            >
              <Icon icon="diagram-tree" iconSize={30} />
              <TabLabel>Pipelines</TabLabel>
            </Tab>
            <Tab to={`/solids`} className={tab === "solids" ? "active" : ""}>
              <Icon icon="git-commit" iconSize={30} />
              <TabLabel>Solids</TabLabel>
            </Tab>
            <Tab to={`/runs`} className={tab === "runs" ? "active" : ""}>
              <Icon icon="history" iconSize={30} />
              <TabLabel>Runs</TabLabel>
            </Tab>
            <Tab
              to={`/playground`}
              className={tab === "playground" ? "active" : ""}
            >
              <Icon icon="manually-entered-data" iconSize={30} />
              <TabLabel>Playground</TabLabel>
            </Tab>
            <Tab
              to={`/scheduler`}
              className={tab === "scheduler" ? "active" : ""}
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
