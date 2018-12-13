import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors, Icon } from "@blueprintjs/core";
import {
  SidebarTitle,
  SidebarSubhead,
  SidebarSection,
  SectionItemContainer,
  SectionItemHeader
} from "./SidebarComponents";
import Description from "./Description";
import Config from "./Config";
import { SidebarPipelineInfoFragment } from "./types/SidebarPipelineInfoFragment";
import { IconNames } from "@blueprintjs/icons";

// TODO (schrockn/bengotow)
// For pipelines with multiple resources this was a tad aggressive,
// so commenting it out for now.
// const NO_DESCRIPTION = "No description provided.";
const NO_DESCRIPTION = "";

interface ISidebarPipelineInfoProps {
  pipeline: SidebarPipelineInfoFragment;
}

export default class SidebarPipelineInfo extends React.Component<
  ISidebarPipelineInfoProps
> {
  static fragments = {
    SidebarPipelineInfoFragment: gql`
      fragment SidebarPipelineInfoFragment on Pipeline {
        name
        description
        contexts {
          name
          description
          config {
            ...ConfigFragment
          }
          resources {
            name
            description
            config {
              ...ConfigFragment
            }
          }
        }
      }

      ${Config.fragments.ConfigFragment}
    `
  };

  render() {
    const { pipeline } = this.props;

    return (
      <div>
        <SidebarSubhead>Pipeline</SidebarSubhead>
        <SidebarTitle>{pipeline.name}</SidebarTitle>
        <SidebarSection title={"Description"}>
          <Description
            description={pipeline ? pipeline.description : NO_DESCRIPTION}
          />
        </SidebarSection>
        <SidebarSection title={"Contexts"}>
          {pipeline.contexts.map(context => (
            <ContextContainer key={context.name}>
              <SectionItemHeader>{context.name}</SectionItemHeader>
              <Description
                description={context.description || NO_DESCRIPTION}
              />
              {context.config && <Config config={context.config} />}
              {context.resources.map(resource => (
                <ContextResourceContainer key={resource.name}>
                  <Icon icon={IconNames.LAYERS} color={Colors.DARK_GRAY2} />
                  <div>
                    <SectionItemHeader>{resource.name}</SectionItemHeader>
                    <Description
                      description={resource.description || NO_DESCRIPTION}
                    />
                    {resource.config && <Config config={resource.config} />}
                  </div>
                </ContextResourceContainer>
              ))}
            </ContextContainer>
          ))}
        </SidebarSection>
      </div>
    );
  }
}

const ContextContainer = styled(SectionItemContainer)`
  border-bottom: 1px solid ${Colors.LIGHT_GRAY2};
  margin-bottom: 20px;
  padding-bottom: 20px;
  &:last-child {
    border-bottom: none;
  }
`;

const ContextResourceContainer = styled.div`
  display: flex;
  align-items: flex-start;
  padding-top: 15px;
  & .bp3-icon {
    padding-top: 10px;
    padding-right: 10px;
  }
`;
