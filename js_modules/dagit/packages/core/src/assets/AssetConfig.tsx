import {gql} from '@apollo/client';

import {
  SidebarAssetQuery_assetNodeOrError_AssetNode_configField as ConfigField,
  SidebarAssetQuery_assetNodeOrError_AssetNode_configField_configType_CompositeConfigType as ConfigSchema,
} from '../asset-graph/types/SidebarAssetQuery';
import {CONFIG_TYPE_SCHEMA_FRAGMENT} from '../typeexplorer/ConfigTypeSchema';

export interface HasConfigField {
  configField: ConfigField | null;
}

export function configSchemaForAssetNode(obj: HasConfigField): ConfigSchema | null {
  if (obj.configField) {
    const configSchema = obj.configField.configType as ConfigSchema;
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
