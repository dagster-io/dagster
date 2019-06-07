import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Link } from "react-router-dom";
import { H6, Text, Code, UL, Button } from "@blueprintjs/core";

import { titleOfIO } from "./Util";
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
import ConfigTypeSchema from "./ConfigTypeSchema";
import { SidebarSolidInfoFragment } from "./types/SidebarSolidInfoFragment";

type SolidLinkInfo = {
  solid: { name: string };
  definition: { name: string };
};

type SolidMappingTable = {
  [key: string]: SolidLinkInfo[];
};

interface ISidebarSolidInfoProps {
  solid: SidebarSolidInfoFragment;
  showingSubsolids: boolean;
  onEnterCompositeSolid: (solidName: string) => void;
}

export default class SidebarSolidInfo extends React.Component<
  ISidebarSolidInfoProps
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
          ... on SolidDefinition {
            configDefinition {
              configType {
                ...ConfigTypeSchemaFragment
              }
            }
          }
          ... on CompositeSolidDefinition {
            inputMappings {
              definition {
                name
              }
              mappedInput {
                definition {
                  name
                }
                solid {
                  name
                }
              }
            }
            outputMappings {
              definition {
                name
              }
              mappedOutput {
                definition {
                  name
                }
                solid {
                  name
                }
              }
            }
          }
        }
        inputs {
          definition {
            name
            description
            type {
              ...RuntimeTypeWithTooltipFragment
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
              ...RuntimeTypeWithTooltipFragment
            }
            expectations {
              name
              description
            }
          }
        }
      }

      ${TypeWithTooltip.fragments.RuntimeTypeWithTooltipFragment}
      ${SolidTypeSignature.fragments.SolidTypeSignatureFragment}
      ${ConfigTypeSchema.fragments.ConfigTypeSchemaFragment}
    `
  };

  public render() {
    const { solid, showingSubsolids, onEnterCompositeSolid } = this.props;
    const { name, definition, inputs, outputs } = solid;

    const Plugin = pluginForMetadata(definition.metadata);

    const isComposite = definition.__typename == "CompositeSolidDefinition";
    const configDefinition =
      definition.__typename == "SolidDefinition"
        ? definition.configDefinition
        : null;

    const inputMappings: SolidMappingTable = {};
    const outputMappings: SolidMappingTable = {};

    if (
      showingSubsolids &&
      definition.__typename == "CompositeSolidDefinition"
    ) {
      definition.inputMappings.forEach(
        m =>
          (inputMappings[m.definition.name] = [
            ...(inputMappings[m.definition.name] || []),
            m.mappedInput
          ])
      );
      definition.outputMappings.forEach(
        m =>
          (outputMappings[m.definition.name] = [
            ...(outputMappings[m.definition.name] || []),
            m.mappedOutput
          ])
      );
    }

    return (
      <div>
        {isComposite && !showingSubsolids && (
          <Button
            icon="zoom-in"
            text="Expand"
            style={{ float: "right", margin: "0 15px" }}
            onClick={() => onEnterCompositeSolid(name)}
          />
        )}
        <SidebarSubhead>
          {isComposite ? "Composite Solid" : "Solid"}
        </SidebarSubhead>
        <SidebarTitle>{name}</SidebarTitle>
        <SidebarSection title={"Type Signature"}>
          <SolidTypeSignature solid={solid} />
        </SidebarSection>
        <SidebarSection title={"Description"}>
          <Description description={definition.description} />
          {Plugin && Plugin.SidebarComponent && (
            <Plugin.SidebarComponent solid={solid} />
          )}
        </SidebarSection>
        {configDefinition && (
          <SidebarSection title={"Config"}>
            <ConfigTypeSchema type={configDefinition.configType} />
          </SidebarSection>
        )}
        <SidebarSection title={"Inputs"}>
          {inputs.map((input, idx) => (
            <SectionItemContainer key={idx}>
              <SectionItemHeader>{input.definition.name}</SectionItemHeader>
              <TypeWrapper>
                <TypeWithTooltip type={input.definition.type} />
              </TypeWrapper>
              <Description description={input.definition.description} />
              <SolidLinks title="Depends on: " items={input.dependsOn} />
              <SolidLinks
                title="Mapped to:"
                items={inputMappings[input.definition.name]}
              />
              <Expectations items={input.definition.expectations} />
            </SectionItemContainer>
          ))}
        </SidebarSection>
        <SidebarSection title={"Outputs"}>
          {outputs.map((output, idx) => (
            <SectionItemContainer key={idx}>
              <SectionItemHeader>{output.definition.name}</SectionItemHeader>
              <TypeWrapper>
                <TypeWithTooltip type={output.definition.type} />
              </TypeWrapper>
              <SolidLinks
                title="Mapped from:"
                items={outputMappings[output.definition.name]}
              />
              <Description description={output.definition.description} />
              <Expectations items={output.definition.expectations} />
            </SectionItemContainer>
          ))}
        </SidebarSection>
      </div>
    );
  }
}

const TypeWrapper = styled.div`
  margin-bottom: 10px;
`;

const SolidLink = (props: SolidLinkInfo) => (
  <Link to={`./${props.solid.name}`} style={{ display: "block" }}>
    <Code>{titleOfIO(props)}</Code>
  </Link>
);

const SolidLinks = (props: { title: string; items: SolidLinkInfo[] }) =>
  props.items && props.items.length ? (
    <Text>
      {props.title}
      {props.items.map((i, idx) => (
        <SolidLink key={idx} {...i} />
      ))}
    </Text>
  ) : null;

const Expectations = (props: {
  items: { name: string; description: string | null }[];
}) => (
  <>
    {props.items.length > 0 && <H6>Expectations</H6>}
    <UL>
      {props.items.map((expectation, i) => (
        <li key={i}>
          {expectation.name}
          <Description description={expectation.description} />
        </li>
      ))}
    </UL>
  </>
);
