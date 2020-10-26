import {gql} from '@apollo/client';
import React from 'react';
import styled from 'styled-components/macro';

import {SolidNode} from 'src/graph/SolidNode';
import {layoutSolid} from 'src/graph/getFullSolidLayout';
import {SolidCardSolidDefinitionFragment} from 'src/solids/types/SolidCardSolidDefinitionFragment';

interface SolidCardProps {
  definition: SolidCardSolidDefinitionFragment;
}

export class SolidCard extends React.Component<SolidCardProps> {
  static fragments = {
    SolidCardSolidDefinitionFragment: gql`
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

      ${SolidNode.fragments.SolidNodeDefinitionFragment}
    `,
  };

  render() {
    const {name, inputDefinitions, outputDefinitions} = this.props.definition;
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
      <SolidCardContainer>
        <SVGContainer width={layout.boundingBox.width} height={layout.boundingBox.height}>
          <SolidNode
            invocation={undefined}
            definition={this.props.definition}
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
        </SVGContainer>
      </SolidCardContainer>
    );
  }
}

const SVGContainer = styled.svg`
  overflow: visible;
  border-radius: 0;
  display: block;
`;

const SolidCardContainer = styled.div`
  flex: 1;
  padding: 20px;
  margin-right: 10px;
  margin-bottom: 10px;
  max-width: 450px;
`;
