import {graphql} from '../graphql';

export const ASSET_TABLE_DEFINITION_FRAGMENT = graphql(`
  fragment AssetTableDefinitionFragment on AssetNode {
    id
    groupName
    isSource
    partitionDefinition {
      description
    }
    description
    repository {
      id
      name
      location {
        id
        name
      }
    }
  }
`);

export const ASSET_TABLE_FRAGMENT = graphql(`
  fragment AssetTableFragment on Asset {
    __typename
    id
    key {
      path
    }
    definition {
      id
      ...AssetTableDefinitionFragment
    }
  }
`);
