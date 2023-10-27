// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunPreviewValidationFragment_InvalidSubsetError_ = {
  __typename: 'InvalidSubsetError';
  message: string;
};

export type RunPreviewValidationFragment_PipelineConfigValidationValid_ = {
  __typename: 'PipelineConfigValidationValid';
};

export type RunPreviewValidationFragment_PipelineNotFoundError_ = {
  __typename: 'PipelineNotFoundError';
  message: string;
};

export type RunPreviewValidationFragment_PythonError_ = {
  __typename: 'PythonError';
  message: string;
  stack: Array<string>;
  errorChain: Array<{
    __typename: 'ErrorChainLink';
    isExplicitLink: boolean;
    error: {__typename: 'PythonError'; message: string; stack: Array<string>};
  }>;
};

export type RunPreviewValidationFragment_RunConfigValidationInvalid_ = {
  __typename: 'RunConfigValidationInvalid';
  errors: Array<
    | {
        __typename: 'FieldNotDefinedConfigError';
        fieldName: string;
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
        fieldNames: Array<string>;
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
        field: {__typename: 'ConfigTypeField'; name: string};
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
        fields: Array<{__typename: 'ConfigTypeField'; name: string}>;
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

export type RunPreviewValidationFragment =
  | RunPreviewValidationFragment_InvalidSubsetError_
  | RunPreviewValidationFragment_PipelineConfigValidationValid_
  | RunPreviewValidationFragment_PipelineNotFoundError_
  | RunPreviewValidationFragment_PythonError_
  | RunPreviewValidationFragment_RunConfigValidationInvalid_;

export type RunPreviewValidationErrors_FieldNotDefinedConfigError_Fragment = {
  __typename: 'FieldNotDefinedConfigError';
  fieldName: string;
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
};

export type RunPreviewValidationErrors_FieldsNotDefinedConfigError_Fragment = {
  __typename: 'FieldsNotDefinedConfigError';
  fieldNames: Array<string>;
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
};

export type RunPreviewValidationErrors_MissingFieldConfigError_Fragment = {
  __typename: 'MissingFieldConfigError';
  reason: Types.EvaluationErrorReason;
  message: string;
  field: {__typename: 'ConfigTypeField'; name: string};
  stack: {
    __typename: 'EvaluationStack';
    entries: Array<
      | {__typename: 'EvaluationStackListItemEntry'; listIndex: number}
      | {__typename: 'EvaluationStackMapKeyEntry'; mapKey: any}
      | {__typename: 'EvaluationStackMapValueEntry'; mapKey: any}
      | {__typename: 'EvaluationStackPathEntry'; fieldName: string}
    >;
  };
};

export type RunPreviewValidationErrors_MissingFieldsConfigError_Fragment = {
  __typename: 'MissingFieldsConfigError';
  reason: Types.EvaluationErrorReason;
  message: string;
  fields: Array<{__typename: 'ConfigTypeField'; name: string}>;
  stack: {
    __typename: 'EvaluationStack';
    entries: Array<
      | {__typename: 'EvaluationStackListItemEntry'; listIndex: number}
      | {__typename: 'EvaluationStackMapKeyEntry'; mapKey: any}
      | {__typename: 'EvaluationStackMapValueEntry'; mapKey: any}
      | {__typename: 'EvaluationStackPathEntry'; fieldName: string}
    >;
  };
};

export type RunPreviewValidationErrors_RuntimeMismatchConfigError_Fragment = {
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
};

export type RunPreviewValidationErrors_SelectorTypeConfigError_Fragment = {
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
};

export type RunPreviewValidationErrorsFragment =
  | RunPreviewValidationErrors_FieldNotDefinedConfigError_Fragment
  | RunPreviewValidationErrors_FieldsNotDefinedConfigError_Fragment
  | RunPreviewValidationErrors_MissingFieldConfigError_Fragment
  | RunPreviewValidationErrors_MissingFieldsConfigError_Fragment
  | RunPreviewValidationErrors_RuntimeMismatchConfigError_Fragment
  | RunPreviewValidationErrors_SelectorTypeConfigError_Fragment;
