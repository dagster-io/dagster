import {gql} from '@apollo/client';
import {Code} from '@dagster-io/ui-components';
import styled from 'styled-components';

import {OpTypeSignatureFragment} from './types/OpTypeSignature.types';
import {breakOnUnderscores} from '../app/Util';
import {DAGSTER_TYPE_WITH_TOOLTIP_FRAGMENT, TypeWithTooltip} from '../typeexplorer/TypeWithTooltip';

interface IOpTypeSignature {
  definition: OpTypeSignatureFragment;
}

export const OpTypeSignature = (props: IOpTypeSignature) => {
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
  padding: 4px;
  box-shadow: none;
  line-height: 20px;
`;
