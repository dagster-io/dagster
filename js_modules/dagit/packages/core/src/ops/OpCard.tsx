import {Box} from '@dagster-io/ui';
import React from 'react';
import styled from 'styled-components/macro';

import {OpNode} from '../graph/OpNode';
import {layoutOp} from '../graph/asyncGraphLayout';
import {graphql} from '../graphql';
import {OpCardSolidDefinitionFragmentFragment} from '../graphql/graphql';

interface OpCardProps {
  definition: OpCardSolidDefinitionFragmentFragment;
}

export const OpCard: React.FC<OpCardProps> = (props) => {
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

export const OP_CARD_SOLID_DEFINITION_FRAGMENT = graphql(`
  fragment OpCardSolidDefinitionFragment on ISolidDefinition {
    ...OpNodeDefinitionFragment
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
`);

const OpCardContainer = styled.div`
  flex: 1;
  max-width: 450px;
  position: relative;
`;
