// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type ResourceDetailsFragment = {
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
    type: Types.NestedResourceType;
    resource: {
      __typename: 'ResourceDetails';
      name: string;
      resourceType: string;
      description: string | null;
    } | null;
  }>;
  parentResources: Array<{
    __typename: 'NestedResourceEntry';
    name: string;
    resource: {
      __typename: 'ResourceDetails';
      name: string;
      resourceType: string;
      description: string | null;
    } | null;
  }>;
  assetKeysUsing: Array<{__typename: 'AssetKey'; path: Array<string>}>;
  jobsOpsUsing: Array<{
    __typename: 'JobWithOps';
    job: {__typename: 'Job'; id: string; name: string};
    opsUsing: Array<{
      __typename: 'SolidHandle';
      handleID: string;
      solid: {__typename: 'Solid'; name: string};
    }>;
  }>;
};

export type ResourceRootQueryVariables = Types.Exact<{
  resourceSelector: Types.ResourceSelector;
}>;

export type ResourceRootQuery = {
  __typename: 'Query';
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
          type: Types.NestedResourceType;
          resource: {
            __typename: 'ResourceDetails';
            name: string;
            resourceType: string;
            description: string | null;
          } | null;
        }>;
        parentResources: Array<{
          __typename: 'NestedResourceEntry';
          name: string;
          resource: {
            __typename: 'ResourceDetails';
            name: string;
            resourceType: string;
            description: string | null;
          } | null;
        }>;
        assetKeysUsing: Array<{__typename: 'AssetKey'; path: Array<string>}>;
        jobsOpsUsing: Array<{
          __typename: 'JobWithOps';
          job: {__typename: 'Job'; id: string; name: string};
          opsUsing: Array<{
            __typename: 'SolidHandle';
            handleID: string;
            solid: {__typename: 'Solid'; name: string};
          }>;
        }>;
      }
    | {__typename: 'ResourceNotFoundError'};
};
