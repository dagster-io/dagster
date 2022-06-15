import {assertUnreachable} from '../app/Util';

import {
  ConfigEditorRunConfigSchemaFragment_allConfigTypes,
  ConfigEditorRunConfigSchemaFragment,
} from './types/ConfigEditorRunConfigSchemaFragment';

export const scaffoldType = (
  configTypeKey: string,
  typeLookup: {[key: string]: ConfigEditorRunConfigSchemaFragment_allConfigTypes},
): any => {
  const type = typeLookup[configTypeKey];

  switch (type.__typename) {
    case 'CompositeConfigType':
      if (type.isSelector) {
        // Could potentially do something better here, like scaffold out
        // all the types and let the user delete the ones they don't want.
        return '<selector>';
      }

      const config = {};
      for (const field of type.fields) {
        const {name, isRequired, configTypeKey} = field;
        if (isRequired) {
          config[name] = scaffoldType(configTypeKey, typeLookup);
        }
      }

      return config;
    case 'ArrayConfigType':
      return [];
    case 'MapConfigType':
      return {};
    case 'NullableConfigType':
      // If a type is nullable we include it in the scaffolded config anyway
      // by using the inner type
      const innerType = type.typeParamKeys[0];
      return scaffoldType(innerType, typeLookup);
    case 'EnumConfigType':
      // Here we just join all the potential enum values with a |. The user needs to delete
      // all the values but the ones they want to use.
      return type.values.map((i) => i.value).join('|');
    case 'ScalarUnionConfigType':
      // Here we just scaffold the scalar value. Could potentially try to
      // scaffold the other type instead.
      const {scalarTypeKey} = type;
      return scaffoldType(scalarTypeKey, typeLookup);
    case 'RegularConfigType':
      return {
        String: '',
        Int: 0,
        Float: 0.0,
        Bool: true,
        Any: 'AnyType',
      }[type.key];
    default:
      assertUnreachable(type);
  }
};

export const createTypeLookup = (
  allConfigTypes: ConfigEditorRunConfigSchemaFragment_allConfigTypes[],
) => {
  const typeLookup: {[key: string]: ConfigEditorRunConfigSchemaFragment_allConfigTypes} = {};
  for (const type of allConfigTypes) {
    typeLookup[type.key] = type;
  }

  return typeLookup;
};

export const scaffoldPipelineConfig = (configSchema: ConfigEditorRunConfigSchemaFragment) => {
  const {allConfigTypes, rootConfigType} = configSchema;
  const typeLookup = createTypeLookup(allConfigTypes);
  const config = scaffoldType(rootConfigType.key, typeLookup);
  return config;
};
