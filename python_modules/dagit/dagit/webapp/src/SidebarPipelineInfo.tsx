import * as React from "react";
import { PipelinesFragment } from "./types/PipelinesFragment";
import {
  SidebarTitle,
  SidebarSubhead,
  SidebarSection,
  SectionItemContainer,
  SectionItemHeader
} from "./SidebarComponents";
import Description from "./Description";
import Config from "./Config";

interface ISidebarPipelineInfoProps {
  pipeline: PipelinesFragment;
}

export default class SidebarPipelineInfo extends React.Component<
  ISidebarPipelineInfoProps
> {
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
            <SectionItemContainer>
              <SectionItemHeader>{context.name}</SectionItemHeader>
              <Description description={context.description} />
              <Config config={context.config} />
            </SectionItemContainer>
          ))}
        </SidebarSection>
      </div>
    );
  }
}
