import {gql} from '@apollo/client';
import {Code, Colors} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components/macro';

import {breakOnUnderscores} from '../app/Util';
import {DAGSTER_TYPE_WITH_TOOLTIP_FRAGMENT, TypeWithTooltip} from '../typeexplorer/TypeWithTooltip';
import {FontFamily} from '../ui/styles';

import {SolidTypeSignatureFragment} from './types/SolidTypeSignatureFragment';

interface ISolidTypeSignature {
  definition: SolidTypeSignatureFragment;
}

export const SolidTypeSignature: React.FC<ISolidTypeSignature> = (props) => {
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

export const SOLID_TYPE_SIGNATURE_FRAGMENT = gql`
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

  ${DAGSTER_TYPE_WITH_TOOLTIP_FRAGMENT}
`;

const TypeSignature = styled(Code)`
  && {
    background: ${Colors.LIGHT_GRAY5};
    font-family: ${FontFamily.monospace};
    font-size: 14px;
    padding: 4px 10px;
    box-shadow: none;
    color: black;
  }
`;
