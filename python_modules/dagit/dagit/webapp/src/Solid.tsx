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
        description
        config {
          ...ConfigFragment
        }
        inputs {
          name
          description
          type {
            ...TypeWithTooltipFragment
          }
          expectations {
            name
            description
          }
          dependsOn {
            name
            solid {
              name
            }
          }
        }
        outputs {
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

      ${TypeWithTooltip.fragments.TypeWithTooltipFragment}
      ${SolidTypeSignature.fragments.SolidTypeSignatureFragment}
      ${Config.fragments.ConfigFragment}
    `
  };

  renderInputs() {
    return this.props.solid.inputs.map((input, i: number) => (
      <SolidPartCard key={i} elevation={3} horizontal={true}>
        <H6>
          Input <Code>{input.name}</Code>
        </H6>
        <TypeWrapper>
          <TypeWithTooltip type={input.type} />
        </TypeWrapper>
        <Description description={input.description} />
        {input.dependsOn && (
          <Text>
            Depends on{" "}
            <Link to={`./${input.dependsOn.name}`}>
              <Code>{input.dependsOn.name}</Code>
            </Link>
          </Text>
        )}
        {input.expectations.length > 0 ? <H6>Expectations</H6> : null}
        <UL>
          {input.expectations.map((expectation, i) => (
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
          Output <Code>{output.name}</Code>
        </H6>
        <TypeWrapper>
          <TypeWithTooltip type={output.type} />
        </TypeWrapper>
        <Description description={output.description} />
        {output.expectations.length > 0 ? <H6>Expectations</H6> : null}
        <UL>
          {output.expectations.map((expectation, i) => (
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
        <H5>
          <Code>{this.props.solid.name}</Code>
        </H5>
        <TypeSignatureWrapper>
          <SolidTypeSignature solid={this.props.solid} />
        </TypeSignatureWrapper>
        <DescriptionWrapper>
          <Description description={this.props.solid.description} />
        </DescriptionWrapper>
        <Config config={this.props.solid.config} />
        <Cards>
          {this.renderInputs()}
          {this.renderSeparator()}
          {this.renderOutputs()}
        </Cards>
      </SpacedCard>
    );
  }
}

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
  max-width: 500px;
`;

const TypeWrapper = styled.div`
  margin-bottom: 10px;
`;
