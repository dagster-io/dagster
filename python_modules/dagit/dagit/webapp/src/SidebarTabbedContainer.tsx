import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Icon, IconName, Colors } from "@blueprintjs/core";
import { Link } from "react-router-dom";
import TypeExplorerContainer from "./configeditor/TypeExplorerContainer";
import TypeListContainer from "./configeditor/TypeListContainer";
import SidebarPipelineInfo from "./SidebarPipelineInfo";
import SidebarSolidInfo from "./SidebarSolidInfo";
import { SidebarTabbedContainerPipelineFragment } from "./types/SidebarTabbedContainerPipelineFragment";
import { SidebarTabbedContainerSolidFragment } from "./types/SidebarTabbedContainerSolidFragment";

interface ISidebarTabbedContainerProps {
  types: string | undefined;
  typeExplorer: string | undefined;
  pipeline: SidebarTabbedContainerPipelineFragment;
  solid: SidebarTabbedContainerSolidFragment | undefined;
}

interface ITabInfo {
  name: string;
  icon: IconName;
  key: string;
  link: string;
}

const TabInfo: Array<ITabInfo> = [
  {
    name: "Info",
    icon: "diagram-tree",
    key: "info",
    link: "?"
  },
  {
    name: "Types",
    icon: "manual",
    key: "types",
    link: "?types=true"
  }
];

export default class SidebarTabbedContainer extends React.Component<
  ISidebarTabbedContainerProps
> {
  static fragments = {
    SidebarTabbedContainerPipelineFragment: gql`
      fragment SidebarTabbedContainerPipelineFragment on Pipeline {
        ...SidebarPipelineInfoFragment
      }

      ${SidebarPipelineInfo.fragments.SidebarPipelineInfoFragment}
    `,
    SidebarTabbedContainerSolidFragment: gql`
      fragment SidebarTabbedContainerSolidFragment on Solid {
        ...SidebarSolidInfoFragment
      }
      ${SidebarSolidInfo.fragments.SidebarSolidInfoFragment}
    `
  };

  render() {
    const { typeExplorer, types, solid, pipeline } = this.props;

    let content = <div />;
    let activeTab = "info";

    if (typeExplorer) {
      activeTab = "types";
      content = (
        <TypeExplorerContainer
          pipelineName={this.props.pipeline.name}
          typeName={typeExplorer}
        />
      );
    } else if (types) {
      activeTab = "types";
      content = <TypeListContainer pipelineName={this.props.pipeline.name} />;
    } else if (solid) {
      content = <SidebarSolidInfo solid={solid} key={solid.name} />;
    } else {
      content = <SidebarPipelineInfo pipeline={pipeline} key={pipeline.name} />;
    }

    return (
      <div>
        <Tabs id="TabsExample">
          {TabInfo.map(({ name, icon, key, link }) => (
            <Link to={link} key={key}>
              <Tab key={key} active={key === activeTab}>
                <Icon icon={icon} style={{ marginRight: 5 }} />
                {name}
              </Tab>
            </Link>
          ))}
        </Tabs>
        {content}
      </div>
    );
  }
}

const Tabs = styled.div`
  width: 100%;
  display: flex;
  margin-top: 10px;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid #ccc;
`;
const Tab = styled.div<{ active: boolean }>`
  color: ${p => (p.active ? Colors.COBALT3 : Colors.GRAY2)}
  border-top: 3px solid transparent;
  border-bottom: 3px solid ${p => (p.active ? Colors.COBALT3 : "transparent")}
  text-decoration: none;
  white-space: nowrap;
  min-width: 40px;
  padding: 0 10px;
  display: flex;
  height: 36px;
  align-items: center;
`;
