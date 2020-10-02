import {Code, Colors} from '@blueprintjs/core';
import gql from 'graphql-tag';
import * as React from 'react';
import styled from 'styled-components/macro';

import {TypeWithTooltip} from 'src/TypeWithTooltip';
import {breakOnUnderscores} from 'src/Util';
import {SolidTypeSignatureFragment} from 'src/types/SolidTypeSignatureFragment';

interface ISolidTypeSignature {
  definition: SolidTypeSignatureFragment;
}

export class SolidTypeSignature extends React.Component<ISolidTypeSignature> {
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
