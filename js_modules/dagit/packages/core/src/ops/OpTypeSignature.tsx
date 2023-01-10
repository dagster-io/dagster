// eslint-disable-next-line no-restricted-imports
import {Code} from '@blueprintjs/core';
import {Colors, FontFamily} from '@dagster-io/ui';
import * as React from 'react';
import styled from 'styled-components/macro';

import {breakOnUnderscores} from '../app/Util';
import {graphql} from '../graphql';
import {OpTypeSignatureFragmentFragment} from '../graphql/graphql';
import {TypeWithTooltip} from '../typeexplorer/TypeWithTooltip';

interface IOpTypeSignature {
  definition: OpTypeSignatureFragmentFragment;
}

export const OpTypeSignature: React.FC<IOpTypeSignature> = (props) => {
  const {inputDefinitions, outputDefinitions} = props.definition;

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
};

export const OP_TYPE_SIGNATURE_FRAGMENT = graphql(`
  fragment OpTypeSignatureFragment on ISolidDefinition {
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
`);

const TypeSignature = styled(Code)`
  && {
    background: ${Colors.Blue50};
    font-family: ${FontFamily.monospace};
    font-size: 14px;
    padding: 4px;
    box-shadow: none;
    color: black;
  }
`;
