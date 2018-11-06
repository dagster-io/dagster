import * as React from "react";
import gql from "graphql-tag";
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
          <Description description={pipeline ? pipeline.description : ""} />
        </SidebarSection>
        <SidebarSection title={"Contexts"}>
          {pipeline.contexts.map(context => (
            <SectionItemContainer key={context.name}>
              <SectionItemHeader>{context.name}</SectionItemHeader>
              <Description description={context.description} />
              {context.config && <Config config={context.config} />}
            </SectionItemContainer>
          ))}
        </SidebarSection>
      </div>
    );
  }
}
