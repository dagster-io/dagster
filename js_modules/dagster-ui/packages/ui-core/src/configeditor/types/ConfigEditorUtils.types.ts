// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type ConfigEditorRunConfigSchemaFragment = {
  __typename: 'RunConfigSchema';
  rootDefaultYaml: string;
  rootConfigType:
    | {__typename: 'ArrayConfigType'; key: string}
    | {__typename: 'CompositeConfigType'; key: string}
    | {__typename: 'EnumConfigType'; key: string}
    | {__typename: 'MapConfigType'; key: string}
    | {__typename: 'NullableConfigType'; key: string}
    | {__typename: 'RegularConfigType'; key: string}
    | {__typename: 'ScalarUnionConfigType'; key: string};
  allConfigTypes: Array<
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
        values: Array<{__typename: 'EnumConfigValue'; value: string; description: string | null}>;
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
        key: string;
        scalarTypeKey: string;
        nonScalarTypeKey: string;
        description: string | null;
        isSelector: boolean;
        typeParamKeys: Array<string>;
      }
  >;
};

export type AllConfigTypesForEditor_ArrayConfigType_Fragment = {
  __typename: 'ArrayConfigType';
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: Array<string>;
};

export type AllConfigTypesForEditor_CompositeConfigType_Fragment = {
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
};

export type AllConfigTypesForEditor_EnumConfigType_Fragment = {
  __typename: 'EnumConfigType';
  givenName: string;
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: Array<string>;
  values: Array<{__typename: 'EnumConfigValue'; value: string; description: string | null}>;
};

export type AllConfigTypesForEditor_MapConfigType_Fragment = {
  __typename: 'MapConfigType';
  keyLabelName: string | null;
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: Array<string>;
};

export type AllConfigTypesForEditor_NullableConfigType_Fragment = {
  __typename: 'NullableConfigType';
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: Array<string>;
};

export type AllConfigTypesForEditor_RegularConfigType_Fragment = {
  __typename: 'RegularConfigType';
  givenName: string;
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: Array<string>;
};

export type AllConfigTypesForEditor_ScalarUnionConfigType_Fragment = {
  __typename: 'ScalarUnionConfigType';
  key: string;
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: Array<string>;
};

export type AllConfigTypesForEditorFragment =
  | AllConfigTypesForEditor_ArrayConfigType_Fragment
  | AllConfigTypesForEditor_CompositeConfigType_Fragment
  | AllConfigTypesForEditor_EnumConfigType_Fragment
  | AllConfigTypesForEditor_MapConfigType_Fragment
  | AllConfigTypesForEditor_NullableConfigType_Fragment
  | AllConfigTypesForEditor_RegularConfigType_Fragment
  | AllConfigTypesForEditor_ScalarUnionConfigType_Fragment;

export type CompositeConfigTypeForSchemaFragment = {
  __typename: 'CompositeConfigType';
  fields: Array<{
    __typename: 'ConfigTypeField';
    name: string;
    description: string | null;
    isRequired: boolean;
    configTypeKey: string;
    defaultValueAsJson: string | null;
  }>;
};

export type ConfigEditorValidationFragment_InvalidSubsetError_ = {__typename: 'InvalidSubsetError'};

export type ConfigEditorValidationFragment_PipelineConfigValidationValid_ = {
  __typename: 'PipelineConfigValidationValid';
};

export type ConfigEditorValidationFragment_PipelineNotFoundError_ = {
  __typename: 'PipelineNotFoundError';
};

export type ConfigEditorValidationFragment_PythonError_ = {__typename: 'PythonError'};

export type ConfigEditorValidationFragment_RunConfigValidationInvalid_ = {
  __typename: 'RunConfigValidationInvalid';
  errors: Array<
    | {
        __typename: 'FieldNotDefinedConfigError';
        reason: Types.EvaluationErrorReason;
        message: string;
        stack: {
          __typename: 'EvaluationStack';
          entries: Array<
            | {__typename: 'EvaluationStackListItemEntry'; listIndex: number}
            | {__typename: 'EvaluationStackMapKeyEntry'; mapKey: any}
            | {__typename: 'EvaluationStackMapValueEntry'; mapKey: any}
            | {__typename: 'EvaluationStackPathEntry'; fieldName: string}
          >;
        };
      }
    | {
        __typename: 'FieldsNotDefinedConfigError';
        reason: Types.EvaluationErrorReason;
        message: string;
        stack: {
          __typename: 'EvaluationStack';
          entries: Array<
            | {__typename: 'EvaluationStackListItemEntry'; listIndex: number}
            | {__typename: 'EvaluationStackMapKeyEntry'; mapKey: any}
            | {__typename: 'EvaluationStackMapValueEntry'; mapKey: any}
            | {__typename: 'EvaluationStackPathEntry'; fieldName: string}
          >;
        };
      }
    | {
        __typename: 'MissingFieldConfigError';
        reason: Types.EvaluationErrorReason;
        message: string;
        stack: {
          __typename: 'EvaluationStack';
          entries: Array<
            | {__typename: 'EvaluationStackListItemEntry'; listIndex: number}
            | {__typename: 'EvaluationStackMapKeyEntry'; mapKey: any}
            | {__typename: 'EvaluationStackMapValueEntry'; mapKey: any}
            | {__typename: 'EvaluationStackPathEntry'; fieldName: string}
          >;
        };
      }
    | {
        __typename: 'MissingFieldsConfigError';
        reason: Types.EvaluationErrorReason;
        message: string;
        stack: {
          __typename: 'EvaluationStack';
          entries: Array<
            | {__typename: 'EvaluationStackListItemEntry'; listIndex: number}
            | {__typename: 'EvaluationStackMapKeyEntry'; mapKey: any}
            | {__typename: 'EvaluationStackMapValueEntry'; mapKey: any}
            | {__typename: 'EvaluationStackPathEntry'; fieldName: string}
          >;
        };
      }
    | {
        __typename: 'RuntimeMismatchConfigError';
        reason: Types.EvaluationErrorReason;
        message: string;
        stack: {
          __typename: 'EvaluationStack';
          entries: Array<
            | {__typename: 'EvaluationStackListItemEntry'; listIndex: number}
            | {__typename: 'EvaluationStackMapKeyEntry'; mapKey: any}
            | {__typename: 'EvaluationStackMapValueEntry'; mapKey: any}
            | {__typename: 'EvaluationStackPathEntry'; fieldName: string}
          >;
        };
      }
    | {
        __typename: 'SelectorTypeConfigError';
        reason: Types.EvaluationErrorReason;
        message: string;
        stack: {
          __typename: 'EvaluationStack';
          entries: Array<
            | {__typename: 'EvaluationStackListItemEntry'; listIndex: number}
            | {__typename: 'EvaluationStackMapKeyEntry'; mapKey: any}
            | {__typename: 'EvaluationStackMapValueEntry'; mapKey: any}
            | {__typename: 'EvaluationStackPathEntry'; fieldName: string}
          >;
        };
      }
  >;
};

export type ConfigEditorValidationFragment =
  | ConfigEditorValidationFragment_InvalidSubsetError_
  | ConfigEditorValidationFragment_PipelineConfigValidationValid_
  | ConfigEditorValidationFragment_PipelineNotFoundError_
  | ConfigEditorValidationFragment_PythonError_
  | ConfigEditorValidationFragment_RunConfigValidationInvalid_;
