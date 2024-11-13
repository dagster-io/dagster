// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type PartitionDefinitionForLaunchAssetFragment = {
  __typename: 'PartitionDefinition';
  description: string;
  type: Types.PartitionDefinitionType;
  name: string | null;
  dimensionTypes: Array<{
    __typename: 'DimensionDefinitionType';
    name: string;
    dynamicPartitionsDefinitionName: string | null;
  }>;
};

export type BackfillPolicyForLaunchAssetFragment = {
  __typename: 'BackfillPolicy';
  maxPartitionsPerRun: number | null;
  description: string;
  policyType: Types.BackfillPolicyType;
};

export type LaunchAssetExecutionAssetNodeFragment = {
  __typename: 'AssetNode';
  id: string;
  opNames: Array<string>;
  jobNames: Array<string>;
  graphName: string | null;
  hasMaterializePermission: boolean;
  isObservable: boolean;
  isExecutable: boolean;
  isMaterializable: boolean;
  partitionDefinition: {
    __typename: 'PartitionDefinition';
    description: string;
    type: Types.PartitionDefinitionType;
    name: string | null;
    dimensionTypes: Array<{
      __typename: 'DimensionDefinitionType';
      name: string;
      dynamicPartitionsDefinitionName: string | null;
    }>;
  } | null;
  backfillPolicy: {
    __typename: 'BackfillPolicy';
    maxPartitionsPerRun: number | null;
    description: string;
    policyType: Types.BackfillPolicyType;
  } | null;
  assetKey: {__typename: 'AssetKey'; path: Array<string>};
  assetChecksOrError:
    | {__typename: 'AssetCheckNeedsAgentUpgradeError'}
    | {__typename: 'AssetCheckNeedsMigrationError'}
    | {__typename: 'AssetCheckNeedsUserCodeUpgrade'}
    | {
        __typename: 'AssetChecks';
        checks: Array<{
          __typename: 'AssetCheck';
          name: string;
          canExecuteIndividually: Types.AssetCheckCanExecuteIndividually;
          jobNames: Array<string>;
        }>;
      };
  dependencyKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
  repository: {
    __typename: 'Repository';
    id: string;
    name: string;
    location: {__typename: 'RepositoryLocation'; id: string; name: string};
  };
  requiredResources: Array<{__typename: 'ResourceRequirement'; resourceKey: string}>;
  configField: {
    __typename: 'ConfigTypeField';
    name: string;
    isRequired: boolean;
    configType:
      | {
          __typename: 'ArrayConfigType';
          key: string;
          description: string | null;
          isSelector: boolean;
          typeParamKeys: Array<string>;
          recursiveConfigTypes: Array<
            | {
                __typename: 'ArrayConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'CompositeConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
                fields: Array<{
                  __typename: 'ConfigTypeField';
                  name: string;
                  description: string | null;
                  isRequired: boolean;
                  configTypeKey: string;
                  defaultValueAsJson: string | null;
                }>;
              }
            | {
                __typename: 'EnumConfigType';
                givenName: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
                values: Array<{
                  __typename: 'EnumConfigValue';
                  value: string;
                  description: string | null;
                }>;
              }
            | {
                __typename: 'MapConfigType';
                keyLabelName: string | null;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'NullableConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'RegularConfigType';
                givenName: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'ScalarUnionConfigType';
                scalarTypeKey: string;
                nonScalarTypeKey: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
          >;
        }
      | {
          __typename: 'CompositeConfigType';
          key: string;
          description: string | null;
          isSelector: boolean;
          typeParamKeys: Array<string>;
          recursiveConfigTypes: Array<
            | {
                __typename: 'ArrayConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'CompositeConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
                fields: Array<{
                  __typename: 'ConfigTypeField';
                  name: string;
                  description: string | null;
                  isRequired: boolean;
                  configTypeKey: string;
                  defaultValueAsJson: string | null;
                }>;
              }
            | {
                __typename: 'EnumConfigType';
                givenName: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
                values: Array<{
                  __typename: 'EnumConfigValue';
                  value: string;
                  description: string | null;
                }>;
              }
            | {
                __typename: 'MapConfigType';
                keyLabelName: string | null;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'NullableConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'RegularConfigType';
                givenName: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'ScalarUnionConfigType';
                scalarTypeKey: string;
                nonScalarTypeKey: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
          >;
          fields: Array<{
            __typename: 'ConfigTypeField';
            name: string;
            description: string | null;
            isRequired: boolean;
            configTypeKey: string;
            defaultValueAsJson: string | null;
          }>;
        }
      | {
          __typename: 'EnumConfigType';
          givenName: string;
          key: string;
          description: string | null;
          isSelector: boolean;
          typeParamKeys: Array<string>;
          recursiveConfigTypes: Array<
            | {
                __typename: 'ArrayConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'CompositeConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
                fields: Array<{
                  __typename: 'ConfigTypeField';
                  name: string;
                  description: string | null;
                  isRequired: boolean;
                  configTypeKey: string;
                  defaultValueAsJson: string | null;
                }>;
              }
            | {
                __typename: 'EnumConfigType';
                givenName: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
                values: Array<{
                  __typename: 'EnumConfigValue';
                  value: string;
                  description: string | null;
                }>;
              }
            | {
                __typename: 'MapConfigType';
                keyLabelName: string | null;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'NullableConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'RegularConfigType';
                givenName: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'ScalarUnionConfigType';
                scalarTypeKey: string;
                nonScalarTypeKey: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
          >;
          values: Array<{__typename: 'EnumConfigValue'; value: string; description: string | null}>;
        }
      | {
          __typename: 'MapConfigType';
          keyLabelName: string | null;
          key: string;
          description: string | null;
          isSelector: boolean;
          typeParamKeys: Array<string>;
          recursiveConfigTypes: Array<
            | {
                __typename: 'ArrayConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'CompositeConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
                fields: Array<{
                  __typename: 'ConfigTypeField';
                  name: string;
                  description: string | null;
                  isRequired: boolean;
                  configTypeKey: string;
                  defaultValueAsJson: string | null;
                }>;
              }
            | {
                __typename: 'EnumConfigType';
                givenName: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
                values: Array<{
                  __typename: 'EnumConfigValue';
                  value: string;
                  description: string | null;
                }>;
              }
            | {
                __typename: 'MapConfigType';
                keyLabelName: string | null;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'NullableConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'RegularConfigType';
                givenName: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'ScalarUnionConfigType';
                scalarTypeKey: string;
                nonScalarTypeKey: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
          >;
        }
      | {
          __typename: 'NullableConfigType';
          key: string;
          description: string | null;
          isSelector: boolean;
          typeParamKeys: Array<string>;
          recursiveConfigTypes: Array<
            | {
                __typename: 'ArrayConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'CompositeConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
                fields: Array<{
                  __typename: 'ConfigTypeField';
                  name: string;
                  description: string | null;
                  isRequired: boolean;
                  configTypeKey: string;
                  defaultValueAsJson: string | null;
                }>;
              }
            | {
                __typename: 'EnumConfigType';
                givenName: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
                values: Array<{
                  __typename: 'EnumConfigValue';
                  value: string;
                  description: string | null;
                }>;
              }
            | {
                __typename: 'MapConfigType';
                keyLabelName: string | null;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'NullableConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'RegularConfigType';
                givenName: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'ScalarUnionConfigType';
                scalarTypeKey: string;
                nonScalarTypeKey: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
          >;
        }
      | {
          __typename: 'RegularConfigType';
          givenName: string;
          key: string;
          description: string | null;
          isSelector: boolean;
          typeParamKeys: Array<string>;
          recursiveConfigTypes: Array<
            | {
                __typename: 'ArrayConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'CompositeConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
                fields: Array<{
                  __typename: 'ConfigTypeField';
                  name: string;
                  description: string | null;
                  isRequired: boolean;
                  configTypeKey: string;
                  defaultValueAsJson: string | null;
                }>;
              }
            | {
                __typename: 'EnumConfigType';
                givenName: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
                values: Array<{
                  __typename: 'EnumConfigValue';
                  value: string;
                  description: string | null;
                }>;
              }
            | {
                __typename: 'MapConfigType';
                keyLabelName: string | null;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'NullableConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'RegularConfigType';
                givenName: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'ScalarUnionConfigType';
                scalarTypeKey: string;
                nonScalarTypeKey: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
          >;
        }
      | {
          __typename: 'ScalarUnionConfigType';
          scalarTypeKey: string;
          nonScalarTypeKey: string;
          key: string;
          description: string | null;
          isSelector: boolean;
          typeParamKeys: Array<string>;
          recursiveConfigTypes: Array<
            | {
                __typename: 'ArrayConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'CompositeConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
                fields: Array<{
                  __typename: 'ConfigTypeField';
                  name: string;
                  description: string | null;
                  isRequired: boolean;
                  configTypeKey: string;
                  defaultValueAsJson: string | null;
                }>;
              }
            | {
                __typename: 'EnumConfigType';
                givenName: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
                values: Array<{
                  __typename: 'EnumConfigValue';
                  value: string;
                  description: string | null;
                }>;
              }
            | {
                __typename: 'MapConfigType';
                keyLabelName: string | null;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'NullableConfigType';
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'RegularConfigType';
                givenName: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
            | {
                __typename: 'ScalarUnionConfigType';
                scalarTypeKey: string;
                nonScalarTypeKey: string;
                key: string;
                description: string | null;
                isSelector: boolean;
                typeParamKeys: Array<string>;
              }
          >;
        };
  } | null;
};

export type LaunchAssetLoaderQueryVariables = Types.Exact<{
  assetKeys: Array<Types.AssetKeyInput> | Types.AssetKeyInput;
}>;

export type LaunchAssetLoaderQuery = {
  __typename: 'Query';
  assetNodes: Array<{
    __typename: 'AssetNode';
    id: string;
    opNames: Array<string>;
    jobNames: Array<string>;
    graphName: string | null;
    hasMaterializePermission: boolean;
    isObservable: boolean;
    isExecutable: boolean;
    isMaterializable: boolean;
    partitionDefinition: {
      __typename: 'PartitionDefinition';
      description: string;
      type: Types.PartitionDefinitionType;
      name: string | null;
      dimensionTypes: Array<{
        __typename: 'DimensionDefinitionType';
        name: string;
        dynamicPartitionsDefinitionName: string | null;
      }>;
    } | null;
    backfillPolicy: {
      __typename: 'BackfillPolicy';
      maxPartitionsPerRun: number | null;
      description: string;
      policyType: Types.BackfillPolicyType;
    } | null;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
    assetChecksOrError:
      | {__typename: 'AssetCheckNeedsAgentUpgradeError'}
      | {__typename: 'AssetCheckNeedsMigrationError'}
      | {__typename: 'AssetCheckNeedsUserCodeUpgrade'}
      | {
          __typename: 'AssetChecks';
          checks: Array<{
            __typename: 'AssetCheck';
            name: string;
            canExecuteIndividually: Types.AssetCheckCanExecuteIndividually;
            jobNames: Array<string>;
          }>;
        };
    dependencyKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
    repository: {
      __typename: 'Repository';
      id: string;
      name: string;
      location: {__typename: 'RepositoryLocation'; id: string; name: string};
    };
    requiredResources: Array<{__typename: 'ResourceRequirement'; resourceKey: string}>;
    configField: {
      __typename: 'ConfigTypeField';
      name: string;
      isRequired: boolean;
      configType:
        | {
            __typename: 'ArrayConfigType';
            key: string;
            description: string | null;
            isSelector: boolean;
            typeParamKeys: Array<string>;
            recursiveConfigTypes: Array<
              | {
                  __typename: 'ArrayConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'CompositeConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                  fields: Array<{
                    __typename: 'ConfigTypeField';
                    name: string;
                    description: string | null;
                    isRequired: boolean;
                    configTypeKey: string;
                    defaultValueAsJson: string | null;
                  }>;
                }
              | {
                  __typename: 'EnumConfigType';
                  givenName: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                  values: Array<{
                    __typename: 'EnumConfigValue';
                    value: string;
                    description: string | null;
                  }>;
                }
              | {
                  __typename: 'MapConfigType';
                  keyLabelName: string | null;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'NullableConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'RegularConfigType';
                  givenName: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'ScalarUnionConfigType';
                  scalarTypeKey: string;
                  nonScalarTypeKey: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
            >;
          }
        | {
            __typename: 'CompositeConfigType';
            key: string;
            description: string | null;
            isSelector: boolean;
            typeParamKeys: Array<string>;
            recursiveConfigTypes: Array<
              | {
                  __typename: 'ArrayConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'CompositeConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                  fields: Array<{
                    __typename: 'ConfigTypeField';
                    name: string;
                    description: string | null;
                    isRequired: boolean;
                    configTypeKey: string;
                    defaultValueAsJson: string | null;
                  }>;
                }
              | {
                  __typename: 'EnumConfigType';
                  givenName: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                  values: Array<{
                    __typename: 'EnumConfigValue';
                    value: string;
                    description: string | null;
                  }>;
                }
              | {
                  __typename: 'MapConfigType';
                  keyLabelName: string | null;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'NullableConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'RegularConfigType';
                  givenName: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'ScalarUnionConfigType';
                  scalarTypeKey: string;
                  nonScalarTypeKey: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
            >;
            fields: Array<{
              __typename: 'ConfigTypeField';
              name: string;
              description: string | null;
              isRequired: boolean;
              configTypeKey: string;
              defaultValueAsJson: string | null;
            }>;
          }
        | {
            __typename: 'EnumConfigType';
            givenName: string;
            key: string;
            description: string | null;
            isSelector: boolean;
            typeParamKeys: Array<string>;
            recursiveConfigTypes: Array<
              | {
                  __typename: 'ArrayConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'CompositeConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                  fields: Array<{
                    __typename: 'ConfigTypeField';
                    name: string;
                    description: string | null;
                    isRequired: boolean;
                    configTypeKey: string;
                    defaultValueAsJson: string | null;
                  }>;
                }
              | {
                  __typename: 'EnumConfigType';
                  givenName: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                  values: Array<{
                    __typename: 'EnumConfigValue';
                    value: string;
                    description: string | null;
                  }>;
                }
              | {
                  __typename: 'MapConfigType';
                  keyLabelName: string | null;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'NullableConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'RegularConfigType';
                  givenName: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'ScalarUnionConfigType';
                  scalarTypeKey: string;
                  nonScalarTypeKey: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
            >;
            values: Array<{
              __typename: 'EnumConfigValue';
              value: string;
              description: string | null;
            }>;
          }
        | {
            __typename: 'MapConfigType';
            keyLabelName: string | null;
            key: string;
            description: string | null;
            isSelector: boolean;
            typeParamKeys: Array<string>;
            recursiveConfigTypes: Array<
              | {
                  __typename: 'ArrayConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'CompositeConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                  fields: Array<{
                    __typename: 'ConfigTypeField';
                    name: string;
                    description: string | null;
                    isRequired: boolean;
                    configTypeKey: string;
                    defaultValueAsJson: string | null;
                  }>;
                }
              | {
                  __typename: 'EnumConfigType';
                  givenName: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                  values: Array<{
                    __typename: 'EnumConfigValue';
                    value: string;
                    description: string | null;
                  }>;
                }
              | {
                  __typename: 'MapConfigType';
                  keyLabelName: string | null;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'NullableConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'RegularConfigType';
                  givenName: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'ScalarUnionConfigType';
                  scalarTypeKey: string;
                  nonScalarTypeKey: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
            >;
          }
        | {
            __typename: 'NullableConfigType';
            key: string;
            description: string | null;
            isSelector: boolean;
            typeParamKeys: Array<string>;
            recursiveConfigTypes: Array<
              | {
                  __typename: 'ArrayConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'CompositeConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                  fields: Array<{
                    __typename: 'ConfigTypeField';
                    name: string;
                    description: string | null;
                    isRequired: boolean;
                    configTypeKey: string;
                    defaultValueAsJson: string | null;
                  }>;
                }
              | {
                  __typename: 'EnumConfigType';
                  givenName: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                  values: Array<{
                    __typename: 'EnumConfigValue';
                    value: string;
                    description: string | null;
                  }>;
                }
              | {
                  __typename: 'MapConfigType';
                  keyLabelName: string | null;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'NullableConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'RegularConfigType';
                  givenName: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'ScalarUnionConfigType';
                  scalarTypeKey: string;
                  nonScalarTypeKey: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
            >;
          }
        | {
            __typename: 'RegularConfigType';
            givenName: string;
            key: string;
            description: string | null;
            isSelector: boolean;
            typeParamKeys: Array<string>;
            recursiveConfigTypes: Array<
              | {
                  __typename: 'ArrayConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'CompositeConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                  fields: Array<{
                    __typename: 'ConfigTypeField';
                    name: string;
                    description: string | null;
                    isRequired: boolean;
                    configTypeKey: string;
                    defaultValueAsJson: string | null;
                  }>;
                }
              | {
                  __typename: 'EnumConfigType';
                  givenName: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                  values: Array<{
                    __typename: 'EnumConfigValue';
                    value: string;
                    description: string | null;
                  }>;
                }
              | {
                  __typename: 'MapConfigType';
                  keyLabelName: string | null;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'NullableConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'RegularConfigType';
                  givenName: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'ScalarUnionConfigType';
                  scalarTypeKey: string;
                  nonScalarTypeKey: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
            >;
          }
        | {
            __typename: 'ScalarUnionConfigType';
            scalarTypeKey: string;
            nonScalarTypeKey: string;
            key: string;
            description: string | null;
            isSelector: boolean;
            typeParamKeys: Array<string>;
            recursiveConfigTypes: Array<
              | {
                  __typename: 'ArrayConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'CompositeConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                  fields: Array<{
                    __typename: 'ConfigTypeField';
                    name: string;
                    description: string | null;
                    isRequired: boolean;
                    configTypeKey: string;
                    defaultValueAsJson: string | null;
                  }>;
                }
              | {
                  __typename: 'EnumConfigType';
                  givenName: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                  values: Array<{
                    __typename: 'EnumConfigValue';
                    value: string;
                    description: string | null;
                  }>;
                }
              | {
                  __typename: 'MapConfigType';
                  keyLabelName: string | null;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'NullableConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'RegularConfigType';
                  givenName: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'ScalarUnionConfigType';
                  scalarTypeKey: string;
                  nonScalarTypeKey: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
            >;
          };
    } | null;
  }>;
  assetNodeAdditionalRequiredKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
  assetNodeDefinitionCollisions: Array<{
    __typename: 'AssetNodeDefinitionCollision';
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
    repositories: Array<{
      __typename: 'Repository';
      id: string;
      name: string;
      location: {__typename: 'RepositoryLocation'; id: string; name: string};
    }>;
  }>;
};

export type LaunchAssetLoaderJobQueryVariables = Types.Exact<{
  job: Types.PipelineSelector;
}>;

export type LaunchAssetLoaderJobQuery = {
  __typename: 'Query';
  assetNodes: Array<{
    __typename: 'AssetNode';
    id: string;
    opNames: Array<string>;
    jobNames: Array<string>;
    graphName: string | null;
    hasMaterializePermission: boolean;
    isObservable: boolean;
    isExecutable: boolean;
    isMaterializable: boolean;
    partitionDefinition: {
      __typename: 'PartitionDefinition';
      description: string;
      type: Types.PartitionDefinitionType;
      name: string | null;
      dimensionTypes: Array<{
        __typename: 'DimensionDefinitionType';
        name: string;
        dynamicPartitionsDefinitionName: string | null;
      }>;
    } | null;
    backfillPolicy: {
      __typename: 'BackfillPolicy';
      maxPartitionsPerRun: number | null;
      description: string;
      policyType: Types.BackfillPolicyType;
    } | null;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
    assetChecksOrError:
      | {__typename: 'AssetCheckNeedsAgentUpgradeError'}
      | {__typename: 'AssetCheckNeedsMigrationError'}
      | {__typename: 'AssetCheckNeedsUserCodeUpgrade'}
      | {
          __typename: 'AssetChecks';
          checks: Array<{
            __typename: 'AssetCheck';
            name: string;
            canExecuteIndividually: Types.AssetCheckCanExecuteIndividually;
            jobNames: Array<string>;
          }>;
        };
    dependencyKeys: Array<{__typename: 'AssetKey'; path: Array<string>}>;
    repository: {
      __typename: 'Repository';
      id: string;
      name: string;
      location: {__typename: 'RepositoryLocation'; id: string; name: string};
    };
    requiredResources: Array<{__typename: 'ResourceRequirement'; resourceKey: string}>;
    configField: {
      __typename: 'ConfigTypeField';
      name: string;
      isRequired: boolean;
      configType:
        | {
            __typename: 'ArrayConfigType';
            key: string;
            description: string | null;
            isSelector: boolean;
            typeParamKeys: Array<string>;
            recursiveConfigTypes: Array<
              | {
                  __typename: 'ArrayConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'CompositeConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                  fields: Array<{
                    __typename: 'ConfigTypeField';
                    name: string;
                    description: string | null;
                    isRequired: boolean;
                    configTypeKey: string;
                    defaultValueAsJson: string | null;
                  }>;
                }
              | {
                  __typename: 'EnumConfigType';
                  givenName: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                  values: Array<{
                    __typename: 'EnumConfigValue';
                    value: string;
                    description: string | null;
                  }>;
                }
              | {
                  __typename: 'MapConfigType';
                  keyLabelName: string | null;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'NullableConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'RegularConfigType';
                  givenName: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'ScalarUnionConfigType';
                  scalarTypeKey: string;
                  nonScalarTypeKey: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
            >;
          }
        | {
            __typename: 'CompositeConfigType';
            key: string;
            description: string | null;
            isSelector: boolean;
            typeParamKeys: Array<string>;
            recursiveConfigTypes: Array<
              | {
                  __typename: 'ArrayConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'CompositeConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                  fields: Array<{
                    __typename: 'ConfigTypeField';
                    name: string;
                    description: string | null;
                    isRequired: boolean;
                    configTypeKey: string;
                    defaultValueAsJson: string | null;
                  }>;
                }
              | {
                  __typename: 'EnumConfigType';
                  givenName: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                  values: Array<{
                    __typename: 'EnumConfigValue';
                    value: string;
                    description: string | null;
                  }>;
                }
              | {
                  __typename: 'MapConfigType';
                  keyLabelName: string | null;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'NullableConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'RegularConfigType';
                  givenName: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'ScalarUnionConfigType';
                  scalarTypeKey: string;
                  nonScalarTypeKey: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
            >;
            fields: Array<{
              __typename: 'ConfigTypeField';
              name: string;
              description: string | null;
              isRequired: boolean;
              configTypeKey: string;
              defaultValueAsJson: string | null;
            }>;
          }
        | {
            __typename: 'EnumConfigType';
            givenName: string;
            key: string;
            description: string | null;
            isSelector: boolean;
            typeParamKeys: Array<string>;
            recursiveConfigTypes: Array<
              | {
                  __typename: 'ArrayConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'CompositeConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                  fields: Array<{
                    __typename: 'ConfigTypeField';
                    name: string;
                    description: string | null;
                    isRequired: boolean;
                    configTypeKey: string;
                    defaultValueAsJson: string | null;
                  }>;
                }
              | {
                  __typename: 'EnumConfigType';
                  givenName: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                  values: Array<{
                    __typename: 'EnumConfigValue';
                    value: string;
                    description: string | null;
                  }>;
                }
              | {
                  __typename: 'MapConfigType';
                  keyLabelName: string | null;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'NullableConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'RegularConfigType';
                  givenName: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'ScalarUnionConfigType';
                  scalarTypeKey: string;
                  nonScalarTypeKey: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
            >;
            values: Array<{
              __typename: 'EnumConfigValue';
              value: string;
              description: string | null;
            }>;
          }
        | {
            __typename: 'MapConfigType';
            keyLabelName: string | null;
            key: string;
            description: string | null;
            isSelector: boolean;
            typeParamKeys: Array<string>;
            recursiveConfigTypes: Array<
              | {
                  __typename: 'ArrayConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'CompositeConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                  fields: Array<{
                    __typename: 'ConfigTypeField';
                    name: string;
                    description: string | null;
                    isRequired: boolean;
                    configTypeKey: string;
                    defaultValueAsJson: string | null;
                  }>;
                }
              | {
                  __typename: 'EnumConfigType';
                  givenName: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                  values: Array<{
                    __typename: 'EnumConfigValue';
                    value: string;
                    description: string | null;
                  }>;
                }
              | {
                  __typename: 'MapConfigType';
                  keyLabelName: string | null;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'NullableConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'RegularConfigType';
                  givenName: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'ScalarUnionConfigType';
                  scalarTypeKey: string;
                  nonScalarTypeKey: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
            >;
          }
        | {
            __typename: 'NullableConfigType';
            key: string;
            description: string | null;
            isSelector: boolean;
            typeParamKeys: Array<string>;
            recursiveConfigTypes: Array<
              | {
                  __typename: 'ArrayConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'CompositeConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                  fields: Array<{
                    __typename: 'ConfigTypeField';
                    name: string;
                    description: string | null;
                    isRequired: boolean;
                    configTypeKey: string;
                    defaultValueAsJson: string | null;
                  }>;
                }
              | {
                  __typename: 'EnumConfigType';
                  givenName: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                  values: Array<{
                    __typename: 'EnumConfigValue';
                    value: string;
                    description: string | null;
                  }>;
                }
              | {
                  __typename: 'MapConfigType';
                  keyLabelName: string | null;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'NullableConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'RegularConfigType';
                  givenName: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'ScalarUnionConfigType';
                  scalarTypeKey: string;
                  nonScalarTypeKey: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
            >;
          }
        | {
            __typename: 'RegularConfigType';
            givenName: string;
            key: string;
            description: string | null;
            isSelector: boolean;
            typeParamKeys: Array<string>;
            recursiveConfigTypes: Array<
              | {
                  __typename: 'ArrayConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'CompositeConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                  fields: Array<{
                    __typename: 'ConfigTypeField';
                    name: string;
                    description: string | null;
                    isRequired: boolean;
                    configTypeKey: string;
                    defaultValueAsJson: string | null;
                  }>;
                }
              | {
                  __typename: 'EnumConfigType';
                  givenName: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                  values: Array<{
                    __typename: 'EnumConfigValue';
                    value: string;
                    description: string | null;
                  }>;
                }
              | {
                  __typename: 'MapConfigType';
                  keyLabelName: string | null;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'NullableConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'RegularConfigType';
                  givenName: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'ScalarUnionConfigType';
                  scalarTypeKey: string;
                  nonScalarTypeKey: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
            >;
          }
        | {
            __typename: 'ScalarUnionConfigType';
            scalarTypeKey: string;
            nonScalarTypeKey: string;
            key: string;
            description: string | null;
            isSelector: boolean;
            typeParamKeys: Array<string>;
            recursiveConfigTypes: Array<
              | {
                  __typename: 'ArrayConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'CompositeConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                  fields: Array<{
                    __typename: 'ConfigTypeField';
                    name: string;
                    description: string | null;
                    isRequired: boolean;
                    configTypeKey: string;
                    defaultValueAsJson: string | null;
                  }>;
                }
              | {
                  __typename: 'EnumConfigType';
                  givenName: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                  values: Array<{
                    __typename: 'EnumConfigValue';
                    value: string;
                    description: string | null;
                  }>;
                }
              | {
                  __typename: 'MapConfigType';
                  keyLabelName: string | null;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'NullableConfigType';
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'RegularConfigType';
                  givenName: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
              | {
                  __typename: 'ScalarUnionConfigType';
                  scalarTypeKey: string;
                  nonScalarTypeKey: string;
                  key: string;
                  description: string | null;
                  isSelector: boolean;
                  typeParamKeys: Array<string>;
                }
            >;
          };
    } | null;
  }>;
};

export type LaunchAssetLoaderResourceQueryVariables = Types.Exact<{
  pipelineName: Types.Scalars['String']['input'];
  repositoryLocationName: Types.Scalars['String']['input'];
  repositoryName: Types.Scalars['String']['input'];
}>;

export type LaunchAssetLoaderResourceQuery = {
  __typename: 'Query';
  resourcesOrError:
    | {__typename: 'InvalidSubsetError'; message: string}
    | {__typename: 'PipelineNotFoundError'; message: string}
    | {__typename: 'PythonError'; message: string}
    | {
        __typename: 'ResourceConnection';
        resources: Array<{
          __typename: 'Resource';
          name: string;
          configField: {__typename: 'ConfigTypeField'; isRequired: boolean} | null;
        }>;
      };
};

export type LaunchAssetCheckUpstreamQueryVariables = Types.Exact<{
  assetKeys: Array<Types.AssetKeyInput> | Types.AssetKeyInput;
}>;

export type LaunchAssetCheckUpstreamQuery = {
  __typename: 'Query';
  assetNodes: Array<{
    __typename: 'AssetNode';
    id: string;
    isMaterializable: boolean;
    opNames: Array<string>;
    graphName: string | null;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
    assetMaterializations: Array<{__typename: 'MaterializationEvent'; runId: string}>;
  }>;
};

export const LaunchAssetLoaderQueryVersion = 'ae6a5d5eaf00ec9eeefaf3e7dc85a7710eb3647608aa00e3ded59877a289d645';

export const LaunchAssetLoaderJobQueryVersion = '112371f3f0c11b7467940b71e83cba8abf678aed019820af94fdee4f99531841';

export const LaunchAssetLoaderResourceQueryVersion = '93f4cbee0c4705015eee5d84a5857b1122e1c3fb7e4f4907f541c43ef6d56176';

export const LaunchAssetCheckUpstreamQueryVersion = 'afb78499f0bf86942fc7f1ff7261c34caec2bd1e4aabb05c95a2db6acc811aaa';
