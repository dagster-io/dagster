import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Code, Colors } from "@blueprintjs/core";
import TypeWithTooltip from "./TypeWithTooltip";
import { SolidTypeSignatureFragment } from "./types/SolidTypeSignatureFragment";

interface ISolidTypeSignature {
  solid: SolidTypeSignatureFragment;
}

export default class SolidTypeSignature extends React.Component<
  ISolidTypeSignature,
  {}
> {
  static fragments = {
    SolidTypeSignatureFragment: gql`
      fragment SolidTypeSignatureFragment on Solid {
        outputs {
          definition {
            name
            type {
              ...RuntimeTypeWithTooltipFragment
            }
          }
        }
        inputs {
          definition {
            name
            type {
              ...RuntimeTypeWithTooltipFragment
            }
          }
        }
      }

      ${TypeWithTooltip.fragments.RuntimeTypeWithTooltipFragment}
    `
  };

  render() {
    const inputSide = this.props.solid.inputs.map((input, i) => (
      <span key={i}>
        {input.definition.name}:{" "}
        <TypeWithTooltip type={input.definition.type} />
        {i < this.props.solid.inputs.length - 1 ? ", " : ""}
      </span>
    ));
    const outputSide = this.props.solid.outputs.map((output, i) => (
      <span key={i}>
        {output.definition.name}:{" "}
        <TypeWithTooltip type={output.definition.type} />
        {i < this.props.solid.outputs.length - 1 ? ", " : ""}
      </span>
    ));
    return (
      <TypeSignature>
        ({inputSide}) ⇒ ({outputSide})
      </TypeSignature>
    );
  }
}

const TypeSignature = styled(Code)`
  && {
    background: ${Colors.LIGHT_GRAY5};
    padding: 5px 10px;
    box-shadow: none;
    color: black;
  }
`;
