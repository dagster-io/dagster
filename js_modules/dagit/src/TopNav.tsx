import * as React from "react";
import { Route } from "react-router";
import styled from "styled-components";
import { Colors, Alignment, Navbar } from "@blueprintjs/core";
import { Link } from "react-router-dom";

import navBarImage from "./images/nav-logo.png";
import WebsocketStatus from "./WebsocketStatus";
import VersionLabel from "./VersionLabel";
import { PipelineJumpBar } from "./PipelineJumpComponents";
import { TopNavPipelinesFragment } from "./types/TopNavPipelinesFragment";
import gql from "graphql-tag";
import FlaggedFeature from "./FlaggedFeature";

export const TopNav = ({
  pipelines
}: {
  pipelines: TopNavPipelinesFragment[];
}) => (
  <Navbar>
    <Navbar.Group align={Alignment.LEFT}>
      <Route
        render={({ history }) => (
          <Navbar.Heading onClick={() => history.push("/")}>
            <img src={navBarImage} style={{ height: 34 }} alt="logo" />
          </Navbar.Heading>
        )}
      />
      <Navbar.Divider />
      <Route
        path="/:pipeline?/:tab?"
        render={({ match: { params }, history }) => (
          <div style={{ display: "flex", alignItems: "center" }}>
            <PipelineJumpBar
              pipelines={pipelines}
              selectedPipeline={pipelines.find(p => p.name === params.pipeline)}
              onItemSelect={pipeline => {
                history.push(`/${pipeline.name}/${params.tab || "explore"}`);
              }}
            />
            {params.pipeline && <Navbar.Divider />}
            {params.pipeline && (
              <Tabs>
                <Tab
                  to={`/${params.pipeline}/explore`}
                  className={params.tab === "explore" ? "active" : ""}
                >
                  Explore
                </Tab>

                <Tab
                  to={`/${params.pipeline}/execute`}
                  className={params.tab === "execute" ? "active" : ""}
                >
                  Execute
                </Tab>

                <Tab
                  to={`/${params.pipeline}/runs`}
                  className={params.tab === "runs" ? "active" : ""}
                >
                  Runs
                </Tab>
                <FlaggedFeature name="experimentalScheduler">
                  <Tab
                    to={`/${params.pipeline}/schedule`}
                    className={params.tab === "schedule" ? "active" : ""}
                  >
                    Schedule
                  </Tab>
                </FlaggedFeature>
              </Tabs>
            )}
          </div>
        )}
      />
    </Navbar.Group>
    <Navbar.Group align={Alignment.RIGHT}>
      <WebsocketStatus />
      <VersionLabel />
    </Navbar.Group>
  </Navbar>
);

TopNav.fragments = {
  TopNavPipelinesFragment: gql`
    fragment TopNavPipelinesFragment on Pipeline {
      ...PipelineJumpBarFragment
    }
    ${PipelineJumpBar.fragments.PipelineJumpBarFragment}
  `
};

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
