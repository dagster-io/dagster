import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Code } from "@blueprintjs/core";
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
          name
          type {
            ...TypeFragment
          }
        }
        inputs {
          name
          type {
            ...TypeFragment
          }
        }
      }

      ${TypeWithTooltip.fragments.TypeFragment}
    `
  };

  render() {
    const inputSide = this.props.solid.inputs.map((input, i) => (
      <span key={i}>
        {input.name}: <TypeWithTooltip type={input.type} />
        {i < this.props.solid.inputs.length - 1 ? ", " : ""}
      </span>
    ));
    const outputSide = this.props.solid.outputs.map((output, i) => (
      <span key={i}>
        {output.name}: <TypeWithTooltip type={output.type} />
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
    padding: 5px;
  }
`;
