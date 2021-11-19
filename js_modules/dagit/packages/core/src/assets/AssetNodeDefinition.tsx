import {gql} from '@apollo/client';
import * as React from 'react';

import {Description} from '../pipelines/Description';

import {AssetNodeDefinitionFragment} from './types/AssetNodeDefinitionFragment';

export const AssetNodeDefinition: React.FC<{assetNode: AssetNodeDefinitionFragment}> = ({
  assetNode,
}) => {
  return (
    <div style={{paddingTop: 16, paddingLeft: 24}}>
      <Description description={assetNode.description} />
    </div>
  );
};

export const ASSET_NODE_DEFINITION_FRAGMENT = gql`
  fragment AssetNodeDefinitionFragment on AssetNode {
    id
    description
  }
`;
