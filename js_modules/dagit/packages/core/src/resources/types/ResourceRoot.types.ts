// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type ResourceRootQueryVariables = Types.Exact<{
  resourceSelector: Types.ResourceSelector;
}>;

export type ResourceRootQuery = {
  __typename: 'DagitQuery';
  topLevelResourceDetailsOrError:
    | {
        __typename: 'PythonError';
        message: string;
        stack: Array<string>;
        errorChain: Array<{
          __typename: 'ErrorChainLink';
          isExplicitLink: boolean;
          error: {__typename: 'PythonError'; message: string; stack: Array<string>};
        }>;
      }
    | {
        __typename: 'ResourceDetails';
        name: string;
        description: string | null;
        resourceType: string;
        configFields: Array<{
          __typename: 'ConfigTypeField';
          name: string;
          description: string | null;
          configTypeKey: string;
          isRequired: boolean;
          defaultValueAsJson: string | null;
        }>;
        configuredValues: Array<{
          __typename: 'ConfiguredValue';
          key: string;
          value: string;
          type: Types.ConfiguredValueType;
        }>;
        nestedResources: Array<{
          __typename: 'NestedResourceEntry';
          name: string;
          resource: {__typename: 'ResourceDetails'; name: string; resourceType: string};
        }>;
      }
    | {__typename: 'ResourceNotFoundError'};
};
