import * as React from 'react';
import gql from 'graphql-tag';
import styled from 'styled-components/macro';
import {Code, Colors} from '@blueprintjs/core';
import TypeWithTooltip from './TypeWithTooltip';
import {SolidTypeSignatureFragment} from './types/SolidTypeSignatureFragment';
import {breakOnUnderscores} from './Util';

interface ISolidTypeSignature {
  definition: SolidTypeSignatureFragment;
}

export default class SolidTypeSignature extends React.Component<ISolidTypeSignature> {
  static fragments = {
    SolidTypeSignatureFragment: gql`
      fragment SolidTypeSignatureFragment on ISolidDefinition {
        outputDefinitions {
          name
          type {
            ...DagsterTypeWithTooltipFragment
          }
        }
        inputDefinitions {
          name
          type {
            ...DagsterTypeWithTooltipFragment
          }
        }
      }

      ${TypeWithTooltip.fragments.DagsterTypeWithTooltipFragment}
    `,
  };

  render() {
    const {inputDefinitions, outputDefinitions} = this.props.definition;

    const inputSide = inputDefinitions.map((input, i) => (
      <span key={i}>
        {breakOnUnderscores(input.name)}: <TypeWithTooltip type={input.type} />
        {i < inputDefinitions.length - 1 ? ', ' : ''}
      </span>
    ));
    const outputSide = outputDefinitions.map((output, i) => (
      <span key={i}>
        {breakOnUnderscores(output.name)}: <TypeWithTooltip type={output.type} />
        {i < outputDefinitions.length - 1 ? ', ' : ''}
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
    font-size: 12px;
    padding: 4px 10px;
    box-shadow: none;
    color: black;
  }
`;
