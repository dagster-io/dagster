import {gql} from '@apollo/client';

import {
  SidebarAssetQuery_assetNodeOrError_AssetNode_configField as ConfigField,
  SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_CompositeConfigType as AssetConfigSchema,
} from '../asset-graph/types/SidebarAssetQuery';
import {CONFIG_TYPE_SCHEMA_FRAGMENT} from '../typeexplorer/ConfigTypeSchema';

export interface HasConfigField {
  configField: ConfigField | null;
}

export function configSchemaForAssetNode(assetNode: HasConfigField): AssetConfigSchema | null {
  if (assetNode.configField) {
    const configSchema = assetNode.configField.configType as AssetConfigSchema;
    if (configSchema.fields) {
      return configSchema.fields.length > 1 ? configSchema : null;
    } else {
      return null;
    }
  } else {
    return null;
  }
}

export const ASSET_NODE_CONFIG_FRAGMENT = gql`
  fragment AssetNodeConfigFragment on AssetNode {
    id
    configField {
      name
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
