import {graphql} from '../graphql';

export const ASSET_NODE_CONFIG_FRAGMENT = graphql(`
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
`);
