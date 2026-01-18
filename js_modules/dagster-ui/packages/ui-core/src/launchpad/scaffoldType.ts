import {ConfigSchema} from '@dagster-io/ui-components/editor';

import {assertUnreachable} from '../app/Util';

export type AllConfigTypes = ConfigSchema['allConfigTypes'][number];

export const scaffoldType = (
  configTypeKey: string,
  typeLookup: {[key: string]: AllConfigTypes},
): object | string | number | boolean | null | undefined => {
  const type = typeLookup[configTypeKey];
  if (!type) {
    return undefined;
  }

  switch (type.__typename) {
    case 'CompositeConfigType':
      if (type.isSelector) {
        // Could potentially do something better here, like scaffold out
        // all the types and let the user delete the ones they don't want.
        return '<selector>';
      }

      return Object.fromEntries(
        type.fields
          .filter((field) => field.isRequired)
          .map((field) => [field.name, scaffoldType(field.configTypeKey, typeLookup)]),
      );
    case 'ArrayConfigType':
      return [];
    case 'MapConfigType':
      return {};
    case 'NullableConfigType':
      // If a type is nullable we include it in the scaffolded config anyway
      // by using the inner type
      const [innerType] = type.typeParamKeys;
      if (!innerType) {
        return undefined;
      }
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

export const createTypeLookup = (allConfigTypes: AllConfigTypes[]) => {
  return Object.fromEntries(allConfigTypes.map((type) => [type.key, type]));
};

export const scaffoldConfig = (configSchema: ConfigSchema) => {
  const {allConfigTypes, rootConfigType} = configSchema;
  const typeLookup = createTypeLookup(allConfigTypes);
  return scaffoldType(rootConfigType.key, typeLookup);
};
