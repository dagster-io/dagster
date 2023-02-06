// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type OpCardSolidDefinitionFragment_CompositeSolidDefinition_ = {
  __typename: 'CompositeSolidDefinition';
  name: string;
  description: string | null;
  id: string;
  metadata: Array<{__typename: 'MetadataItemDefinition'; key: string; value: string}>;
  inputDefinitions: Array<{
    __typename: 'InputDefinition';
    name: string;
    type:
      | {__typename: 'ListDagsterType'; displayName: string}
      | {__typename: 'NullableDagsterType'; displayName: string}
      | {__typename: 'RegularDagsterType'; displayName: string};
  }>;
  outputDefinitions: Array<{
    __typename: 'OutputDefinition';
    name: string;
    isDynamic: boolean | null;
    type:
      | {__typename: 'ListDagsterType'; displayName: string}
      | {__typename: 'NullableDagsterType'; displayName: string}
      | {__typename: 'RegularDagsterType'; displayName: string};
  }>;
  inputMappings: Array<{
    __typename: 'InputMapping';
    definition: {__typename: 'InputDefinition'; name: string};
    mappedInput: {
      __typename: 'Input';
      definition: {__typename: 'InputDefinition'; name: string};
      solid: {__typename: 'Solid'; name: string};
    };
  }>;
  outputMappings: Array<{
    __typename: 'OutputMapping';
    definition: {__typename: 'OutputDefinition'; name: string};
    mappedOutput: {
      __typename: 'Output';
      definition: {__typename: 'OutputDefinition'; name: string};
      solid: {__typename: 'Solid'; name: string};
    };
  }>;
  assetNodes: Array<{
    __typename: 'AssetNode';
    id: string;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
  }>;
};

export type OpCardSolidDefinitionFragment_SolidDefinition_ = {
  __typename: 'SolidDefinition';
  name: string;
  description: string | null;
  metadata: Array<{__typename: 'MetadataItemDefinition'; key: string; value: string}>;
  inputDefinitions: Array<{
    __typename: 'InputDefinition';
    name: string;
    type:
      | {__typename: 'ListDagsterType'; displayName: string}
      | {__typename: 'NullableDagsterType'; displayName: string}
      | {__typename: 'RegularDagsterType'; displayName: string};
  }>;
  outputDefinitions: Array<{
    __typename: 'OutputDefinition';
    name: string;
    isDynamic: boolean | null;
    type:
      | {__typename: 'ListDagsterType'; displayName: string}
      | {__typename: 'NullableDagsterType'; displayName: string}
      | {__typename: 'RegularDagsterType'; displayName: string};
  }>;
  configField: {
    __typename: 'ConfigTypeField';
    configType:
      | {__typename: 'ArrayConfigType'; key: string; description: string | null}
      | {__typename: 'CompositeConfigType'; key: string; description: string | null}
      | {__typename: 'EnumConfigType'; key: string; description: string | null}
      | {__typename: 'MapConfigType'; key: string; description: string | null}
      | {__typename: 'NullableConfigType'; key: string; description: string | null}
      | {__typename: 'RegularConfigType'; key: string; description: string | null}
      | {__typename: 'ScalarUnionConfigType'; key: string; description: string | null};
  } | null;
  assetNodes: Array<{
    __typename: 'AssetNode';
    id: string;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
  }>;
};

export type OpCardSolidDefinitionFragment =
  | OpCardSolidDefinitionFragment_CompositeSolidDefinition_
  | OpCardSolidDefinitionFragment_SolidDefinition_;
