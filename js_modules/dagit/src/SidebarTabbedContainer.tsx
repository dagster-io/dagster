import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Icon, IconName, Colors } from "@blueprintjs/core";
import { Link } from "react-router-dom";
import { TypeExplorerContainer } from "./typeexplorer/TypeExplorerContainer";
import { TypeListContainer } from "./typeexplorer/TypeListContainer";
import SidebarPipelineInfo from "./SidebarPipelineInfo";
import { SidebarSolidInvocation } from "./SidebarSolidInvocation";
import { SidebarSolidDefinition } from "./SidebarSolidDefinition";
import { SidebarTabbedContainerPipelineFragment } from "./types/SidebarTabbedContainerPipelineFragment";
import { SidebarTabbedContainerSolidFragment } from "./types/SidebarTabbedContainerSolidFragment";
import { SolidNameOrPath } from "./PipelineExplorer";

interface ISidebarTabbedContainerProps {
  types?: string;
  typeExplorer?: string;
  pipeline: SidebarTabbedContainerPipelineFragment;
  solid?: SidebarTabbedContainerSolidFragment;
  parentSolid?: SidebarTabbedContainerSolidFragment;
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
      fragment SidebarTabbedContainerPipelineFragment on Pipeline {
        name
        ...SidebarPipelineInfoFragment
      }

      ${SidebarPipelineInfo.fragments.SidebarPipelineInfoFragment}
    `,
    SidebarTabbedContainerSolidFragment: gql`
      fragment SidebarTabbedContainerSolidFragment on Solid {
        ...SidebarSolidInvocationFragment
        definition {
          __typename
          ...SidebarSolidDefinitionFragment
        }
      }
      ${SidebarSolidInvocation.fragments.SidebarSolidInvocationFragment}
      ${SidebarSolidDefinition.fragments.SidebarSolidDefinitionFragment}
    `
  };

  render() {
    const {
      typeExplorer,
      types,
      solid,
      getInvocations,
      parentSolid,
      pipeline
    } = this.props;

    let content = <div />;
    let activeTab = "info";

    if (typeExplorer) {
      activeTab = "types";
      content = (
        <TypeExplorerContainer
          pipelineName={pipeline.name}
          typeName={typeExplorer}
        />
      );
    } else if (types) {
      activeTab = "types";
      content = <TypeListContainer pipelineName={pipeline.name} />;
    } else if (solid) {
      content = (
        <>
          <SidebarSolidInvocation
            key={`${solid.name}-inv`}
            solid={solid}
            onEnterCompositeSolid={
              solid.definition.__typename === "CompositeSolidDefinition"
                ? this.props.onEnterCompositeSolid
                : undefined
            }
          />
          <SidebarSolidDefinition
            key={`${solid.name}-def`}
            showingSubsolids={false}
            definition={solid.definition}
            getInvocations={getInvocations}
            onClickInvocation={({ handleID }) =>
              this.props.onClickSolid({ path: handleID.split(".") })
            }
          />
        </>
      );
    } else if (parentSolid) {
      content = (
        <>
          <SidebarSolidInvocation
            key={`${parentSolid.name}-inv`}
            solid={parentSolid}
          />
          <SidebarSolidDefinition
            key={`${parentSolid.name}-def`}
            showingSubsolids={true}
            definition={parentSolid.definition}
            getInvocations={getInvocations}
            onClickInvocation={({ handleID }) =>
              this.props.onClickSolid({ path: handleID.split(".") })
            }
          />
        </>
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
  border-bottom: 3px solid ${p => (p.active ? Colors.COBALT3 : "transparent")}
  text-decoration: none;
  white-space: nowrap;
  min-width: 40px;
  padding: 0 10px;
  display: flex;
  height: 36px;
  align-items: center;
`;
