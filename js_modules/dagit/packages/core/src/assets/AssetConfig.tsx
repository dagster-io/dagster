import {gql} from '@apollo/client';

import {CONFIG_TYPE_SCHEMA_FRAGMENT} from '../typeexplorer/ConfigTypeSchema';

export const ASSET_NODE_CONFIG_FRAGMENT = gql`
  fragment AssetNodeConfigFragment on AssetNode {
    id
    configField {
      name
      isRequired
      configType {
        ...ConfigTypeSchemaFragment
        recursiveConfigTypes {
          ...ConfigTypeSchemaFragment
        }
      }
    }
  }
  ${CONFIG_TYPE_SCHEMA_FRAGMENT}
`;
