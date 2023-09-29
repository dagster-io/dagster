import {DocumentNode} from '@apollo/client';
import {MockedResponse} from '@apollo/client/testing';
import deepmerge from 'deepmerge';
import {GraphQLError} from 'graphql';

export function buildQueryMock<
  TQuery extends {__typename: 'Query'},
  TVariables extends Record<string, any>,
>({
  query,
  variables,
  data,
  errors,
  ...rest
}: Partial<Omit<MockedResponse, 'result'>> & {
  query: DocumentNode;
  variables: TVariables;
  data?: Omit<TQuery, '__typename'>;
  errors?: ReadonlyArray<GraphQLError>;
}): MockedResponse<TQuery> {
  return {
    request: {
      query,
      variables,
    },
    result: {
      data: data
        ? ({
            __typename: 'Query',
            ...data,
          } as TQuery)
        : undefined,
      errors,
    },
    ...rest,
  };
}

export function buildMutationMock<
  TMutation extends {__typename: 'Mutation'},
  TVariables extends Record<string, any>,
>({
  query,
  variables,
  data,
  errors,
  ...rest
}: Partial<Omit<MockedResponse, 'result'>> & {
  query: DocumentNode;
  variables: TVariables;
  data?: Omit<TMutation, '__typename'>;
  errors?: ReadonlyArray<GraphQLError>;
}): MockedResponse<TMutation> {
  return {
    request: {
      query,
      variables,
    },
    result: {
      data: data
        ? ({
            __typename: 'Mutation',
            ...data,
          } as TMutation)
        : undefined,
      errors,
    },
    ...rest,
  };
}

export function getMockResultFn<T>(mock: MockedResponse<T>) {
  const result = mock.result!;
  let mockFn;
  if (typeof result === 'function') {
    mockFn = jest.fn(result);
  } else {
    mockFn = jest.fn(() => result!);
  }
  mock.result = mockFn;
  return mockFn;
}

/**
 * Merges result data for queries of the same type.
 * See mocking.test.ts for example usage
 */
export function mergeMockQueries<T extends Record<string, any>>(
  defaultData: MockedResponse<T>,
  ...queries: Array<MockedResponse<T>>
): MockedResponse<T> {
  let mergedResult = resultData(queries[0]!.result);
  for (let i = 1; i < queries.length; i++) {
    mergedResult = deepmerge(
      mergedResult,
      removeDefaultValues(resultData(defaultData.result!), resultData(queries[i]!.result!)),
    );
  }
  return {
    ...queries[0]!,
    result: mergedResult,
  };
}

function resultData<T>(result: MockedResponse<T>['result']) {
  if (result instanceof Function) {
    return result()!;
  } else {
    return result!;
  }
}

function removeDefaultValues<T extends Record<string | number, any> | Array<any>>(
  defaultData: T,
  data: T,
): T {
  const dataWithoutDefaultValues: Partial<T> =
    defaultData instanceof Array ? ([...(data as any)] as T) : {...data}; // Use a copy of 'data'

  if (data instanceof Object) {
    Object.keys(defaultData).forEach((key: any) => {
      if (key in data && key in defaultData) {
        if (data[key] === defaultData[key]) {
          delete dataWithoutDefaultValues[key];
        } else {
          if (data[key] instanceof Object) {
            const dataKey = key as keyof T; // Use a type assertion to narrow the type of key
            const result = removeDefaultValues(defaultData[key], data[key]);
            if (result) {
              dataWithoutDefaultValues[dataKey] = result;
            } else {
              delete dataWithoutDefaultValues[dataKey];
            }
          } else {
            dataWithoutDefaultValues[key] = data[key];
          }
        }
      }
    });
  } else if (data === defaultData) {
    return undefined as any; // Return 'undefined' with 'any' type for consistency
  }

  return dataWithoutDefaultValues as T; // Cast to the original type 'T'
}
