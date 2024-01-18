import {gql} from '@apollo/client';
import {Box} from '@dagster-io/ui-components';
import React from 'react';
import styled from 'styled-components';

import {OpCardSolidDefinitionFragment} from './types/OpCard.types';
import {OP_NODE_DEFINITION_FRAGMENT, OpNode} from '../graph/OpNode';
import {layoutOp} from '../graph/asyncGraphLayout';

interface OpCardProps {
  definition: OpCardSolidDefinitionFragment;
}

export const OpCard = (props: OpCardProps) => {
  const {name, inputDefinitions, outputDefinitions} = props.definition;
  const layout = layoutOp(
    {
      name,
      inputs: inputDefinitions.map((d) => ({
        definition: d,
        dependsOn: [],
      })),
      outputs: outputDefinitions.map((d) => ({
        definition: d,
        dependedBy: [],
      })),
      definition: {
        description: null,
        assetNodes: [],
      },
    },
    {x: 0, y: 0},
  );

  return (
    <Box padding={24}>
      <OpCardContainer style={{height: layout.bounds.height}}>
        <OpNode
          invocation={undefined}
          definition={props.definition}
          minified={false}
          onClick={() => {}}
          onDoubleClick={() => {}}
          onEnterComposite={() => {}}
          onHighlightEdges={() => {}}
          layout={layout}
          selected={false}
          focused={false}
          highlightedEdges={[]}
          dim={false}
        />
      </OpCardContainer>
    </Box>
  );
};

export const OP_CARD_SOLID_DEFINITION_FRAGMENT = gql`
  fragment OpCardSolidDefinitionFragment on ISolidDefinition {
    name
    description
    metadata {
      key
      value
    }
    inputDefinitions {
      name
    }
    outputDefinitions {
      name
    }
    ...OpNodeDefinitionFragment
  }

  ${OP_NODE_DEFINITION_FRAGMENT}
`;

const OpCardContainer = styled.div`
  flex: 1;
  max-width: 450px;
  position: relative;
`;
