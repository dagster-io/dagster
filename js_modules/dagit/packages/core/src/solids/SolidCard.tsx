import {gql} from '@apollo/client';
import React from 'react';
import styled from 'styled-components/macro';

import {SolidNode, SOLID_NODE_DEFINITION_FRAGMENT} from '../graph/SolidNode';
import {layoutSolid} from '../graph/getFullSolidLayout';
import {Box} from '../ui/Box';

import {SolidCardSolidDefinitionFragment} from './types/SolidCardSolidDefinitionFragment';

interface SolidCardProps {
  definition: SolidCardSolidDefinitionFragment;
}

export const SolidCard: React.FC<SolidCardProps> = (props) => {
  const {name, inputDefinitions, outputDefinitions} = props.definition;
  const layout = layoutSolid(
    {
      name: name,
      inputs: inputDefinitions.map((d) => ({
        definition: d,
        dependsOn: [],
      })),
      outputs: outputDefinitions.map((d) => ({
        definition: d,
        dependedBy: [],
      })),
    },
    {x: 0, y: 0},
  );

  return (
    <Box padding={24}>
      <SolidCardContainer style={{height: layout.boundingBox.height}}>
        <SolidNode
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
      </SolidCardContainer>
    </Box>
  );
};

export const SOLID_CARD_SOLID_DEFINITION_FRAGMENT = gql`
  fragment SolidCardSolidDefinitionFragment on ISolidDefinition {
    ...SolidNodeDefinitionFragment
    __typename
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
  }

  ${SOLID_NODE_DEFINITION_FRAGMENT}
`;

const SolidCardContainer = styled.div`
  flex: 1;
  max-width: 450px;
  position: relative;
`;
