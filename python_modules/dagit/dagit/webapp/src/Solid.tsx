import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Link } from "react-router-dom";
import { H5, H6, Text, Colors, Code, UL } from "@blueprintjs/core";
import Config from "./Config";
import SpacedCard from "./SpacedCard";
import SolidTypeSignature from "./SolidTypeSignature";
import TypeWithTooltip from "./TypeWithTooltip";
import Description from "./Description";
import { SolidFragment } from "./types/SolidFragment";

interface ISolidProps {
  solid: SolidFragment;
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
      <SolidPartCard key={i} elevation={3} horizontal={true}>
        <H6>
          Input <Code>{input.definition.name}</Code>
        </H6>
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
            <li>
              {expectation.name}
              <Description description={expectation.description} />
            </li>
          ))}
        </UL>
      </SolidPartCard>
    ));
  }

  renderOutputs() {
    return this.props.solid.outputs.map((output, i: number) => (
      <SolidPartCard key={i} elevation={3} horizontal={true}>
        <H6>
          Output <Code>{output.definition.name}</Code>
        </H6>
        <TypeWrapper>
          <TypeWithTooltip type={output.definition.type} />
        </TypeWrapper>
        <Description description={output.definition.description} />
        {output.definition.expectations.length > 0 ? (
          <H6>Expectations</H6>
        ) : null}
        <UL>
          {output.definition.expectations.map((expectation, i) => (
            <li>
              {expectation.name}
              <Description description={expectation.description} />
            </li>
          ))}
        </UL>
      </SolidPartCard>
    ));
  }

  renderSeparator() {
    if (
      this.props.solid.inputs.length > 0 &&
      this.props.solid.outputs.length > 0
    ) {
      return <CardSeparator />;
    } else {
      return null;
    }
  }

  public render() {
    return (
      <SpacedCard elevation={2}>
        <TypeSignatureWrapper>
          <SolidTypeSignature solid={this.props.solid} />
        </TypeSignatureWrapper>
        <SolidHeader>{this.props.solid.name}</SolidHeader>
        <DescriptionWrapper>
          <Description description={this.props.solid.definition.description} />
        </DescriptionWrapper>
        <Config config={this.props.solid.definition.configDefinition} />
        <Cards>
          {this.renderInputs()}
          {this.renderSeparator()}
          {this.renderOutputs()}
        </Cards>
      </SpacedCard>
    );
  }
}

const SolidHeader = styled.h3`
  font-family: "Source Code Pro", monospace;
  margin-bottom: 8px;
  margin-top: 0;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const Cards = styled.div`
  display: flex;
  flex-wrap: wrap;
  align-items: stretch;
`;

const CardSeparator = styled.div`
  flex: 0 0 1px;
  background-color: ${Colors.LIGHT_GRAY3};
  margin-right: 10px;
`;

const SolidPartCard = styled(SpacedCard)`
  width: 400px;
  margin-bottom: 10px;
`;

const TypeSignatureWrapper = styled.div`
  margin-bottom: 10px;
`;

const DescriptionWrapper = styled.div`
  margin-bottom: 10px;
`;

const TypeWrapper = styled.div`
  margin-bottom: 10px;
`;
