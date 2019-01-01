import * as React from "react";
import { Route } from "react-router";
import styled from "styled-components";
import { Colors, Alignment, Navbar } from "@blueprintjs/core";
import { Link } from "react-router-dom";
import gql from "graphql-tag";

import navBarImage from "./images/nav-logo.png";
import WebsocketStatus from "./WebsocketStatus";
import VersionLabel from "./VersionLabel";
import FlaggedFeature from "./FlaggedFeature";
import { PipelineJumpBar } from "./PipelineJumpComponents";
import { TopNavPipelinesFragment } from "./types/TopNavPipelinesFragment";

export const TopNav = ({
  pipelines
}: {
  pipelines: TopNavPipelinesFragment[];
}) => (
  <Route
    path="/:tab?/:pipeline?"
    render={({ match: { params }, history }) => (
      <Navbar>
        <Navbar.Group align={Alignment.LEFT}>
          <Navbar.Heading onClick={() => history.push("/")}>
            <img src={navBarImage} style={{ height: 34 }} alt="logo" />
          </Navbar.Heading>
          <Navbar.Divider />
          <div style={{ display: "flex", alignItems: "center" }}>
            <PipelineJumpBar
              pipelines={pipelines}
              selectedPipeline={pipelines.find(p => p.name === params.pipeline)}
              onItemSelect={pipeline => {
                const target = params.tab === "execute" ? "execute" : "explore";
                history.push(`/${target}/${pipeline.name}`);
              }}
            />
            {params.pipeline && <Navbar.Divider />}
            {params.pipeline && (
              <Tabs>
                <Tab
                  to={`/explore/${params.pipeline}`}
                  className={params.tab === "explore" ? "active" : ""}
                >
                  Explore
                </Tab>

                <Tab
                  to={`/execute/${params.pipeline}`}
                  className={params.tab === "execute" ? "active" : ""}
                >
                  Execute
                </Tab>
              </Tabs>
            )}
          </div>
        </Navbar.Group>
        <Navbar.Group align={Alignment.RIGHT}>
          <Tab to={`/runs`} className={params.tab === "runs" ? "active" : ""}>
            Runs
          </Tab>
          <FlaggedFeature name="experimentalScheduler">
            <Tab
              to={`/schedule`}
              className={params.tab === "schedule" ? "active" : ""}
            >
              Schedule
            </Tab>
          </FlaggedFeature>

          <Navbar.Divider />

          <WebsocketStatus />
          <VersionLabel />
        </Navbar.Group>
      </Navbar>
    )}
  />
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
