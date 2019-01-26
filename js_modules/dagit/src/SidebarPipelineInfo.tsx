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
import ConfigTypeSchema from "./ConfigTypeSchema";
import { SidebarPipelineInfoFragment } from "./types/SidebarPipelineInfoFragment";
import { IconNames } from "@blueprintjs/icons";

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
            configType {
              ...ConfigTypeSchemaFragment
            }
          }
          resources {
            name
            description
            config {
              configType {
                ...ConfigTypeSchemaFragment
              }
            }
          }
        }
      }

      ${ConfigTypeSchema.fragments.ConfigTypeSchemaFragment}
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
            <SectionItemContainer key={context.name}>
              <SectionItemHeader>{context.name}</SectionItemHeader>
              <Description
                description={context.description || NO_DESCRIPTION}
              />
              {context.config && (
                <ConfigTypeSchema type={context.config.configType} />
              )}
              {context.resources.map(resource => (
                <ContextResourceContainer key={resource.name}>
                  <Icon
                    iconSize={14}
                    icon={IconNames.LAYERS}
                    color={Colors.DARK_GRAY2}
                  />
                  <div>
                    <ContextResourceHeader>
                      {resource.name}
                    </ContextResourceHeader>
                    <Description
                      description={resource.description || NO_DESCRIPTION}
                    />
                    {resource.config && (
                      <ConfigTypeSchema type={resource.config.configType} />
                    )}
                  </div>
                </ContextResourceContainer>
              ))}
            </SectionItemContainer>
          ))}
        </SidebarSection>
      </div>
    );
  }
}

const ContextResourceHeader = styled(SectionItemHeader)`
  font-size: 13px;
`;

const ContextResourceContainer = styled.div`
  display: flex;
  align-items: flex-start;
  padding-top: 15px;
  & .bp3-icon {
    padding-top: 7px;
    padding-right: 10px;
  }
`;
