import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { H5, H6, Text, Colors, Code } from "@blueprintjs/core";
import Argumented from "./Argumented";
import SpacedCard from "./SpacedCard";
import { SolidFragment } from "./types/SolidFragment";

interface ISolidProps {
  solid: SolidFragment;
}

export default class Solid extends React.Component<ISolidProps, {}> {
  static fragments = {
    SolidFragment: gql`
      fragment SolidFragment on Solid {
        name
        description
        inputs {
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
    `
  };

  renderInputs() {
    return this.props.solid.inputs.map((input: any, i: number) => (
      <InputCard key={i} elevation={3}>
        <H6>
          Input <Code>{input.name}</Code>
        </H6>
        <Text>{input.description}</Text>
        {input.dependsOn && (
          <Text>
            Depends on <Code>{input.dependsOn.name}</Code>
          </Text>
        )}
        {input.sources.map((source: any, i: number) => (
          <Argumented
            key={i}
            item={source}
            renderCard={props => <SourceCard {...props} />}
          />
        ))}
      </InputCard>
    ));
  }

  renderOutput() {
    return (
      <OutputCard elevation={3} key="output">
        <H6>Output</H6>
        {this.props.solid.output.materializations.map(
          (materialization: any, i: number) => (
            <Argumented
              key={i}
              item={materialization}
              renderCard={props => <MaterializationCard {...props} />}
            />
          )
        )}
      </OutputCard>
    );
  }

  public render() {
    return (
      <SolidCard elevation={2} horizontal={true}>
        <H5>
          <Code>{this.props.solid.name}</Code>
        </H5>
        <Text>{this.props.solid.description}</Text>
        {this.renderInputs()}
        {this.renderOutput()}
      </SolidCard>
    );
  }
}

const SolidCard = styled(SpacedCard)`
  width: 400px;
`;

const InputCard = styled(SpacedCard)`
  && {
    background-color: ${Colors.FOREST5};
  }
`;

const SourceCard = styled(SpacedCard)`
  && {
    background-color: ${Colors.GREEN5};
  }
`;

const OutputCard = styled(SpacedCard)`
  && {
    background-color: ${Colors.BLUE5};
  }
`;

const MaterializationCard = styled(SpacedCard)`
  && {
    background-color: ${Colors.TURQUOISE5};
  }
`;
