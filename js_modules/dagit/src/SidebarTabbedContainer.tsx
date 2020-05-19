import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components/macro";
import { Icon, IconName, Colors } from "@blueprintjs/core";
import { Link } from "react-router-dom";
import { TypeExplorerContainer } from "./typeexplorer/TypeExplorerContainer";
import { TypeListContainer } from "./typeexplorer/TypeListContainer";
import { SidebarTabbedContainerPipelineFragment } from "./types/SidebarTabbedContainerPipelineFragment";
import { SidebarSolidContainer } from "./SidebarSolidContainer";
import SidebarPipelineInfo from "./SidebarPipelineInfo";
import { SolidNameOrPath } from "./PipelineExplorer";
import { PipelineSelector } from "./PipelineSelectorUtils";

interface ISidebarTabbedContainerProps {
  types?: string;
  typeExplorer?: string;
  pipeline: SidebarTabbedContainerPipelineFragment;
  selector: PipelineSelector;
  solidHandleID?: string;
  parentSolidHandleID?: string;
  getInvocations?: (definitionName: string) => { handleID: string }[];
  onEnterCompositeSolid: (arg: SolidNameOrPath) => void;
  onClickSolid: (arg: SolidNameOrPath) => void;
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
      fragment SidebarTabbedContainerPipelineFragment on IPipelineSnapshot {
        name
        ...SidebarPipelineInfoFragment
      }

      ${SidebarPipelineInfo.fragments.SidebarPipelineInfoFragment}
    `
  };

  render() {
    const {
      typeExplorer,
      types,
      pipeline,
      selector,
      solidHandleID,
      getInvocations,
      parentSolidHandleID,
      onEnterCompositeSolid,
      onClickSolid
    } = this.props;

    let content = <div />;
    let activeTab = "info";

    if (typeExplorer) {
      activeTab = "types";
      content = (
        <TypeExplorerContainer selector={selector} typeName={typeExplorer} />
      );
    } else if (types) {
      activeTab = "types";
      content = <TypeListContainer selector={selector} />;
    } else if (solidHandleID) {
      content = (
        <SidebarSolidContainer
          key={solidHandleID}
          selector={selector}
          handleID={solidHandleID}
          showingSubsolids={false}
          getInvocations={getInvocations}
          onEnterCompositeSolid={onEnterCompositeSolid}
          onClickSolid={onClickSolid}
        />
      );
    } else if (parentSolidHandleID) {
      content = (
        <SidebarSolidContainer
          key={parentSolidHandleID}
          selector={selector}
          handleID={parentSolidHandleID}
          showingSubsolids={true}
          getInvocations={getInvocations}
          onEnterCompositeSolid={onEnterCompositeSolid}
          onClickSolid={onClickSolid}
        />
      );
    } else {
      content = <SidebarPipelineInfo pipeline={pipeline} key={pipeline.name} />;
    }

    return (
      <>
        <Tabs>
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
      </>
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
  border-bottom: 3px solid ${p => (p.active ? Colors.COBALT3 : "transparent")};
  text-decoration: none;
  white-space: nowrap;
  min-width: 40px;
  padding: 0 10px;
  display: flex;
  height: 36px;
  align-items: center;
`;
