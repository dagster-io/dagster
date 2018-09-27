import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { History } from "history";
import { Route } from "react-router";
import { withRouter, Link } from "react-router-dom";
import {
  Tabs,
  ITabsProps,
  Tab,
  NonIdealState,
  Colors
} from "@blueprintjs/core";
import { parse as parseQueryString } from "query-string";
import Pipeline from "./Pipeline";
import Sidebar from "./Sidebar";
import TypeExplorerContainer from "./configeditor/TypeExplorerContainer";
import TypeListContainer from "./configeditor/TypeListContainer";
import { PipelinesFragment } from "./types/PipelinesFragment";

interface IPipelinesProps {
  history: History;
  pipelines: Array<PipelinesFragment>;
  selectedPipeline: string;
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

  handleTabChange = (newTabId: string, oldTabId: string) => {
    if (newTabId === oldTabId) {
      this.props.history.push("/");
    } else {
      this.props.history.push(`/${newTabId}`);
    }
  };

  renderTabs() {
    return this.props.pipelines.map((pipeline, i) => (
      <Tab id={pipeline.name} key={i}>
        {pipeline.name}
      </Tab>
    ));
  }

  renderPipeline() {
    if (this.props.selectedPipeline !== null) {
      const pipeline = this.props.pipelines.find(
        ({ name }) => name === this.props.selectedPipeline
      );
      if (pipeline) {
        return <Pipeline pipeline={pipeline} />;
      }
    }

    return (
      <NonIdealState
        title="No pipeline selected"
        description="Select a pipeline in the sidebar on the left"
      />
    );
  }

  renderSidebar() {
    if (this.props.selectedPipeline !== null) {
      const pipeline = this.props.pipelines.find(
        ({ name }) => name === this.props.selectedPipeline
      );
      if (pipeline) {
        return (
          <Route
            children={({ location }) => {
              if (location.pathname.endsWith("config-editor")) {
                return null;
              } else if (location.search) {
                const search = parseQueryString(location.search);
                let sidebarContents = null;
                if (search.typeExplorer !== null) {
                  sidebarContents = (
                    <TypeExplorerContainer
                      pipelineName={this.props.selectedPipeline}
                      typeName={search.typeExplorer}
                    />
                  );
                }
                return (
                  <Sidebar
                    onClose={() => {
                      this.props.history.push(
                        `/${this.props.selectedPipeline}`
                      );
                    }}
                  >
                    {sidebarContents}
                    <Spacer />
                    <TypeListContainer
                      pipelineName={this.props.selectedPipeline}
                    />
                  </Sidebar>
                );
              }

              return (
                <OpenSidebarButton to={{ search: "?typeExplorer" }}>
                  Docs
                </OpenSidebarButton>
              );
            }}
          />
        );
      }
    }

    return null;
  }

  public render() {
    return (
      <PipelinesContainer>
        <LeftTabs
          id="PipelinesTabs"
          onChange={this.handleTabChange}
          selectedTabId={this.props.selectedPipeline}
          vertical={true}
        >
          {this.renderTabs()}
        </LeftTabs>
        {this.renderPipeline()}
        {this.renderSidebar()}
      </PipelinesContainer>
    );
  }
}

const PipelinesContainer = styled.div`
  flex: 1 1;
  display: flex;
  width: 100%;
`;

// XXX(freiksenet): Some weirdness caused by weird blueprint type hierarchy
const LeftTabs = styled((Tabs as any) as React.StatelessComponent<ITabsProps>)`
  background: ${Colors.LIGHT_GRAY4};
`;

const OpenSidebarButton = styled(Link)`
  position: fixed;
  right: 0;
  top: 10%;
  width: 40px;
  line-height: 40px;
  padding: 20px 0;
  height: auto;
  background-color: ${Colors.GREEN5};
  writing-mode: vertical-rl;
  text-orientation: mixed;
  font-size: 30px;
  text-transform: uppercase;
  cursor: pointer;
  text-decoration: none;
  color: black;

  &:hover {
    text-decoration: none;
    color: black;
  }
`;

const Spacer = styled.div`
  flex: 0 0 5px;
`;
