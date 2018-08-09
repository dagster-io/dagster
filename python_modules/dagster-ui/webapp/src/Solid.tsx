import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Link } from "react-router-dom";
import { H5, H6, Text, Colors, Code, UL } from "@blueprintjs/core";
import Argumented from "./Argumented";
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
        inputs {
          type {
            ...TypeFragment
          }
          expectations {
            name
            description
          }
          name
          description
          sources {
            ...SourceFragment
          }
          dependsOn {
            name
          }
        }
        output {
          type {
            ...TypeFragment
          }
          expectations {
            name
            description
          }
          materializations {
            ...MaterializationFragment
          }
          expectations {
            name
            description
          }
        }
      }

      ${Argumented.fragments.SourceFragment}
      ${Argumented.fragments.MaterializationFragment}
      ${TypeWithTooltip.fragments.TypeFragment}
      ${SolidTypeSignature.fragments.SolidTypeSignatureFragment}
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
              {expectation.name} - {expectation.description}
            </li>
          ))}
        </UL>
        {input.sources.length > 0 ? <H6>Sources</H6> : null}
        {input.sources.map((source: any, i: number) => (
          <Argumented
            key={i}
            item={source}
            renderCard={props => <SpacedCard {...props} />}
          />
        ))}
      </SolidPartCard>
    ));
  }

  renderOutput() {
    return (
      <SolidPartCard elevation={3} key="output" horizontal={true}>
        <H6>Output</H6>
        <TypeWrapper>
          <TypeWithTooltip type={this.props.solid.output.type} />
        </TypeWrapper>
        {this.props.solid.output.expectations.length > 0 ? (
          <H6>Expectations</H6>
        ) : null}
        <UL>
          {this.props.solid.output.expectations.map((expectation, i) => (
            <li>
              {expectation.name} {expectation.description ? "-" : ""}{" "}
              {expectation.description}
            </li>
          ))}
        </UL>
        {this.props.solid.output.materializations.length > 0 ? (
          <H6>Materializations</H6>
        ) : null}
        {this.props.solid.output.materializations.map(
          (materialization: any, i: number) => (
            <Argumented
              key={i}
              item={materialization}
              renderCard={props => <SpacedCard {...props} />}
            />
          )
        )}
      </SolidPartCard>
    );
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
        <Cards>
          {this.renderInputs()}
          <CardSeparator />
          {this.renderOutput()}
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
