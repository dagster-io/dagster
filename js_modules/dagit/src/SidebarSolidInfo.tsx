import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Link } from "react-router-dom";
import { Icon, Text, Code, Button, Colors } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";

import { titleOfIO } from "./Util";
import { pluginForMetadata } from "./plugins";
import SolidTypeSignature from "./SolidTypeSignature";
import TypeWithTooltip from "./TypeWithTooltip";
import {
  SidebarSection,
  SidebarDivider,
  SectionHeader,
  SidebarTitle,
  SidebarSubhead,
  SectionSmallHeader,
  SectionItemContainer
} from "./SidebarComponents";
import Description from "./Description";
import ConfigTypeSchema from "./ConfigTypeSchema";
import { SidebarSolidInfoFragment } from "./types/SidebarSolidInfoFragment";
import { SolidNameOrPath } from "./PipelineExplorer";
import { SolidColumn } from "./runs/LogsRowComponents";

type SolidLinkInfo = {
  solid: { name: string };
  definition: { name: string };
};

type SolidMappingTable = {
  [key: string]: SolidLinkInfo[];
};

interface ISidebarSolidInfoProps {
  solid: SidebarSolidInfoFragment;
  solidDefinitionInvocations?: {
    handleID: string;
    solid: SidebarSolidInfoFragment;
  }[];
  showingSubsolids: boolean;
  onEnterCompositeSolid: (arg: SolidNameOrPath) => void;
  onClickSolid: (arg: SolidNameOrPath) => void;
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
          name
          description
          metadata {
            key
            value
          }
          requiredResources {
            resourceKey
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
          }
          dependedBy {
            definition {
              name
            }
            solid {
              name
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
    const {
      solid,
      solidDefinitionInvocations,
      showingSubsolids,
      onClickSolid,
      onEnterCompositeSolid
    } = this.props;
    const { name, definition, inputs, outputs } = solid;

    const Plugin = pluginForMetadata(definition.metadata);

    const isComposite = definition.__typename === "CompositeSolidDefinition";
    const configDefinition =
      definition.__typename === "SolidDefinition"
        ? definition.configDefinition
        : null;

    const inputMappings: SolidMappingTable = {};
    const outputMappings: SolidMappingTable = {};

    if (
      showingSubsolids &&
      definition.__typename === "CompositeSolidDefinition"
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

    const hasRequiredResources =
      definition.requiredResources && definition.requiredResources.length;
    return (
      <div>
        <SidebarSection title={"Invocation"}>
          <SidebarTitle>{name}</SidebarTitle>
          <DependencyTable>
            <tbody>
              {solid.inputs.map(({ definition, dependsOn }) =>
                dependsOn.map((source, idx) => (
                  <DependencyRow key={idx} from={source} to={definition.name} />
                ))
              )}
              {solid.outputs.map(({ definition, dependedBy }) =>
                dependedBy.map((target, idx) => (
                  <DependencyRow key={idx} from={definition.name} to={target} />
                ))
              )}
            </tbody>
          </DependencyTable>
        </SidebarSection>
        <SidebarDivider />
        <SidebarSection title={"Definition"}>
          {isComposite && !showingSubsolids && (
            <Button
              icon="zoom-in"
              text="Expand"
              style={{ float: "right", margin: "0 15px" }}
              onClick={() => onEnterCompositeSolid({ name })}
            />
          )}
          <SidebarSubhead>
            {isComposite ? "Composite Solid" : "Solid"}
          </SidebarSubhead>
          <SidebarTitle>{definition.name}</SidebarTitle>
          <SolidTypeSignature solid={solid} />
        </SidebarSection>
        {definition.description && (
          <SidebarSection title={"Description"}>
            <Description description={definition.description} />
          </SidebarSection>
        )}
        {definition.metadata && Plugin && Plugin.SidebarComponent && (
          <SidebarSection title={"Metadata"}>
            <Plugin.SidebarComponent solid={solid} />
          </SidebarSection>
        )}
        {configDefinition && (
          <SidebarSection title={"Config"}>
            <ConfigTypeSchema type={configDefinition.configType} />
          </SidebarSection>
        )}
        {hasRequiredResources && (
          <SidebarSection title={"Required Resources"}>
            {definition.requiredResources.sort().map(requirement => (
              <ResourceContainer key={requirement.resourceKey}>
                <Icon
                  iconSize={14}
                  icon={IconNames.LAYERS}
                  color={Colors.DARK_GRAY2}
                />
                <ResourceHeader>{requirement.resourceKey}</ResourceHeader>
              </ResourceContainer>
            ))}
          </SidebarSection>
        )}
        <SidebarSection title={"Inputs"}>
          {inputs.map((input, idx) => (
            <SectionItemContainer key={idx}>
              <SectionSmallHeader>{input.definition.name}</SectionSmallHeader>
              <TypeWrapper>
                <TypeWithTooltip type={input.definition.type} />
              </TypeWrapper>
              <Description description={input.definition.description} />
              <SolidLinks title="Depends on: " items={input.dependsOn} />
              <SolidLinks
                title="Mapped to:"
                items={inputMappings[input.definition.name]}
              />
            </SectionItemContainer>
          ))}
        </SidebarSection>
        <SidebarSection title={"Outputs"}>
          {outputs.map((output, idx) => (
            <SectionItemContainer key={idx}>
              <SectionSmallHeader>{output.definition.name}</SectionSmallHeader>
              <TypeWrapper>
                <TypeWithTooltip type={output.definition.type} />
              </TypeWrapper>
              <SolidLinks
                title="Mapped from:"
                items={outputMappings[output.definition.name]}
              />
              <Description description={output.definition.description} />
            </SectionItemContainer>
          ))}
        </SidebarSection>
        {solidDefinitionInvocations && (
          <SidebarSection title={"All Invocations"}>
            {solidDefinitionInvocations.map(({ solid, handleID }, idx) => (
              <Invocation
                key={idx}
                solid={solid}
                handleID={handleID}
                onClick={() => onClickSolid({ path: handleID.split(".") })}
              />
            ))}
          </SidebarSection>
        )}
      </div>
    );
  }
}

const TypeWrapper = styled.div`
  margin-bottom: 10px;
`;

const SolidLink = (props: SolidLinkInfo) => (
  <Link to={`./${props.solid.name}`}>
    <Code
      style={{
        display: "inline-block",
        verticalAlign: "middle",
        textOverflow: "ellipsis",
        overflow: "hidden",
        maxWidth: "100%"
      }}
    >
      {titleOfIO(props)}
    </Code>
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

const Invocation = (props: {
  onClick: () => void;
  solid: SidebarSolidInfoFragment;
  handleID: string;
}) => {
  const handlePath = props.handleID.split(".");
  return (
    <InvocationContainer onClick={props.onClick}>
      <SolidColumn stepKey={handlePath.join(".")} />
    </InvocationContainer>
  );
};

const DependencyRow = ({
  from,
  to
}: {
  from: SolidLinkInfo | string;
  to: SolidLinkInfo | string;
}) => {
  return (
    <tr>
      <td
        style={{
          whiteSpace: "nowrap",
          maxWidth: 0,
          width: "45%"
        }}
      >
        {typeof from === "string" ? (
          <DependencyLocalIOName>{from}</DependencyLocalIOName>
        ) : (
          <SolidLink {...from} />
        )}
      </td>
      <td>{DependencyArrow}</td>
      <td
        style={{
          textOverflow: "ellipsis",
          overflow: "hidden",
          whiteSpace: "nowrap",
          maxWidth: 0,
          width: "60%"
        }}
      >
        {typeof to === "string" ? (
          <DependencyLocalIOName>{to}</DependencyLocalIOName>
        ) : (
          <SolidLink {...to} />
        )}
      </td>
    </tr>
  );
};

const ResourceHeader = styled(SectionHeader)`
  font-size: 13px;
`;

const ResourceContainer = styled.div`
  display: flex;
  align-items: flex-start;
  padding-top: 15px;
  & .bp3-icon {
    padding-top: 7px;
    padding-right: 10px;
  }
  &:first-child {
    padding-top: 0;
  }
`;

const DependencyLocalIOName = styled.div`
  font-family: monospace;
  font-size: smaller;
  font-weight: 500;
  color: ${Colors.BLACK};
`;

const DependencyTable = styled.table`
  width: 100%;
`;

const InvocationContainer = styled.div`
  margin: 0 -10px;
  padding: 10px;
  pointer: default;
  border-bottom: 1px solid ${Colors.LIGHT_GRAY2};
  &:last-child {
    border-bottom: none;
  }
  &:hover {
    background: ${Colors.LIGHT_GRAY5};
  }
  font-family: monospace;
`;

const DependencyArrow = (
  <svg width="36px" height="9px" viewBox="0 0 36 9" version="1.1">
    <g opacity="0.682756696">
      <g
        transform="translate(-1127.000000, -300.000000)"
        fill="#979797"
        fillRule="nonzero"
      >
        <g transform="translate(120.000000, 200.000000)">
          <path d="M1033.16987,105 L1007.67526,105 L1007.67526,104 L1033.16987,104 L1033.16987,100 L1042.16987,104.5 L1033.16987,109 L1033.16987,105 Z" />
        </g>
      </g>
    </g>
  </svg>
);
