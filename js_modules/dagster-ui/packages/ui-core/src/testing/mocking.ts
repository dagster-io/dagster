import {MockedResponse} from '@apollo/client/testing';
import {GraphQLError} from 'graphql';

import {DocumentNode, OperationVariables} from '../apollo-client';

export function buildQueryMock<
  TQuery extends {__typename: 'Query'},
  TVariables extends OperationVariables,
>({
  query,
  variables,
  data,
  errors,
  ...rest
}: Partial<Omit<MockedResponse, 'result'>> & {
  query: DocumentNode;
  variables?: TVariables;
  data?: Omit<TQuery, '__typename'>;
  errors?: ReadonlyArray<GraphQLError>;
}): Omit<MockedResponse<TQuery>, 'newData'> {
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
}): Omit<MockedResponse<TMutation>, 'newData'> {
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
  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  const result = mock.result!;
  let mockFn;
  if (typeof result === 'function') {
    mockFn = jest.fn(result);
  } else {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    mockFn = jest.fn(() => result!);
  }
  mock.result = mockFn;
  return mockFn;
}

let nativeGBRC: any;

/* simulate getBoundingCLientRect returning a > 0x0 size, important for
testing React trees that useVirtualized()
*/
export function mockViewportClientRect() {
  if (nativeGBRC) {
    return;
  }
  nativeGBRC = window.Element.prototype.getBoundingClientRect;
  window.Element.prototype.getBoundingClientRect = jest
    .fn()
    .mockReturnValue({height: 400, width: 400});
}

export function restoreViewportClientRect() {
  if (!nativeGBRC) {
    return;
  }
  window.Element.prototype.getBoundingClientRect = nativeGBRC;
  nativeGBRC = null;
}
