import {gql} from '@apollo/client';
// eslint-disable-next-line no-restricted-imports
import {Code} from '@blueprintjs/core';
import {Colors, FontFamily} from '@dagster-io/ui';
import * as React from 'react';
import styled from 'styled-components/macro';

import {breakOnUnderscores} from '../app/Util';
import {DAGSTER_TYPE_WITH_TOOLTIP_FRAGMENT, TypeWithTooltip} from '../typeexplorer/TypeWithTooltip';

import {OpTypeSignatureFragment} from './types/OpTypeSignatureFragment';

interface IOpTypeSignature {
  definition: OpTypeSignatureFragment;
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

export const OP_TYPE_SIGNATURE_FRAGMENT = gql`
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

  ${DAGSTER_TYPE_WITH_TOOLTIP_FRAGMENT}
`;

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
