import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Link } from "react-router-dom";
import {
  H5,
  H6,
  Text,
  Colors,
  Code,
  UL,
  Collapse,
  Button
} from "@blueprintjs/core";
import Config from "./Config";
import SolidTypeSignature from "./SolidTypeSignature";
import TypeWithTooltip from "./TypeWithTooltip";
import Description from "./Description";
import { SolidFragment } from "./types/SolidFragment";

interface ISolidProps {
  solid: SolidFragment;
}

class Section extends React.Component<{ title: string }, { isOpen: boolean }> {
  state = {
    isOpen: true
  };

  render() {
    return (
      <div>
        <SectionHeader
          onClick={() => this.setState({ isOpen: !this.state.isOpen })}
        >
          {this.props.title}
        </SectionHeader>
        <Collapse isOpen={this.state.isOpen}>
          <SectionInner>{this.props.children}</SectionInner>
        </Collapse>
      </div>
    );
  }
}

export default class Solid extends React.Component<ISolidProps, {}> {
  static fragments = {
    SolidFragment: gql`
      fragment SolidFragment on Solid {
        ...SolidTypeSignatureFragment
        name
        definition {
          description
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
      <IOItemContainer key={i}>
        <IOHeader>{input.definition.name}</IOHeader>
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
      </IOItemContainer>
    ));
  }

  renderOutputs() {
    return this.props.solid.outputs.map((output, i: number) => (
      <IOItemContainer key={i}>
        <IOHeader>{output.definition.name}</IOHeader>
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
      </IOItemContainer>
    ));
  }

  public render() {
    return (
      <div>
        <SolidHeader>{this.props.solid.name}</SolidHeader>
        <Section title={"Type Signature"}>
          <SolidTypeSignature solid={this.props.solid} />
        </Section>
        <Section title={"Description"}>
          <Description description={this.props.solid.definition.description} />
        </Section>
        {this.props.solid.definition.configDefinition && (
          <Section title={"Config"}>
            <Config config={this.props.solid.definition.configDefinition} />
          </Section>
        )}
        <Section title={"Inputs"}>{this.renderInputs()}</Section>
        <Section title={"Outputs"}>{this.renderOutputs()}</Section>
      </div>
    );
  }
}

const SectionHeader = styled.div`
  padding: 6px;
  padding-left: 12px;
  background: linear-gradient(
    to bottom,
    ${Colors.LIGHT_GRAY5},
    ${Colors.LIGHT_GRAY4}
  );
  border-top: 1px solid ${Colors.LIGHT_GRAY4};
  border-bottom: 1px solid ${Colors.LIGHT_GRAY3};
  color: ${Colors.GRAY1};
  text-transform: uppercase;
  font-size: 0.75rem;
`;

const SectionInner = styled.div`
  padding: 12px;
`;

const SolidHeader = styled.h3`
  font-family: "Source Code Pro", monospace;
  margin-bottom: 2px;
  margin-top: 8px;
  overflow: hidden;
  padding: 12px;
  text-overflow: ellipsis;
`;

const IOHeader = styled.h4`
  font-family: "Source Code Pro", monospace;
  margin: 8px 0;
`;

const IOItemContainer = styled.div`
  margin-bottom: 10px;
`;

const TypeWrapper = styled.div`
  margin-bottom: 10px;
`;
