import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Link } from "react-router-dom";
import { H6, Text, Code, UL } from "@blueprintjs/core";
import { pluginForMetadata } from "./plugins";

import SolidTypeSignature from "./SolidTypeSignature";
import TypeWithTooltip from "./TypeWithTooltip";
import {
  SidebarSection,
  SidebarTitle,
  SidebarSubhead,
  SectionItemHeader,
  SectionItemContainer
} from "./SidebarComponents";
import Description from "./Description";
import Config from "./Config";
import { SidebarSolidInfoFragment } from "./types/SidebarSolidInfoFragment";

interface ISidebarSolidInfoProps {
  solid: SidebarSolidInfoFragment;
}

export default class SidebarSolidInfo extends React.Component<
  ISidebarSolidInfoProps,
  {}
> {
  static fragments = {
    SidebarSolidInfoFragment: gql`
      fragment SidebarSolidInfoFragment on Solid {
        ...SolidTypeSignatureFragment
        name
        definition {
          description
          metadata {
            key
            value
          }
          configDefinition {
            ...ConfigFragment
          }
        }
        inputs {
          definition {
            name
            description
            type {
              ...TypeWithTooltipFragment
            }
            expectations {
              name
              description
            }
          }
          dependsOn {
            definition {
              name
            }
            solid {
              name
            }
          }
        }
        outputs {
          definition {
            name
            description
            type {
              ...TypeWithTooltipFragment
            }
            expectations {
              name
              description
            }
          }
        }
      }

      ${TypeWithTooltip.fragments.TypeWithTooltipFragment}
      ${SolidTypeSignature.fragments.SolidTypeSignatureFragment}
      ${Config.fragments.ConfigFragment}
    `
  };

  renderInputs() {
    return this.props.solid.inputs.map((input, i: number) => (
      <SectionItemContainer key={i}>
        <SectionItemHeader>{input.definition.name}</SectionItemHeader>
        <TypeWrapper>
          <TypeWithTooltip type={input.definition.type} />
        </TypeWrapper>
        <Description description={input.definition.description} />
        {input.dependsOn && (
          <Text>
            Depends on{" "}
            <Link to={`./${input.dependsOn.definition.name}`}>
              <Code>{input.dependsOn.definition.name}</Code>
            </Link>
          </Text>
        )}
        {input.definition.expectations.length > 0 ? (
          <H6>Expectations</H6>
        ) : null}
        <UL>
          {input.definition.expectations.map((expectation, i) => (
            <li key={i}>
              {expectation.name}
              <Description description={expectation.description} />
            </li>
          ))}
        </UL>
      </SectionItemContainer>
    ));
  }

  renderOutputs() {
    return this.props.solid.outputs.map((output, i: number) => (
      <SectionItemContainer key={i}>
        <SectionItemHeader>{output.definition.name}</SectionItemHeader>
        <TypeWrapper>
          <TypeWithTooltip type={output.definition.type} />
        </TypeWrapper>
        <Description description={output.definition.description} />
        {output.definition.expectations.length > 0 ? (
          <H6>Expectations</H6>
        ) : null}
        <UL>
          {output.definition.expectations.map((expectation, i) => (
            <li key={i}>
              {expectation.name}
              <Description description={expectation.description} />
            </li>
          ))}
        </UL>
      </SectionItemContainer>
    ));
  }

  public render() {
    const { solid } = this.props;
    const Plugin = pluginForMetadata(solid.definition.metadata);

    return (
      <div>
        <SidebarSubhead>Solid</SidebarSubhead>
        <SidebarTitle>{solid.name}</SidebarTitle>
        <SidebarSection title={"Type Signature"}>
          <SolidTypeSignature solid={solid} />
        </SidebarSection>
        <SidebarSection title={"Description"}>
          <Description description={solid.definition.description} />
          {Plugin &&
            Plugin.SidebarComponent && (
              <Plugin.SidebarComponent solid={solid} />
            )}
        </SidebarSection>
        {solid.definition.configDefinition && (
          <SidebarSection title={"Config"}>
            <Config config={solid.definition.configDefinition} />
          </SidebarSection>
        )}
        <SidebarSection title={"Inputs"}>{this.renderInputs()}</SidebarSection>
        <SidebarSection title={"Outputs"}>
          {this.renderOutputs()}
        </SidebarSection>
      </div>
    );
  }
}

const TypeWrapper = styled.div`
  margin-bottom: 10px;
`;
