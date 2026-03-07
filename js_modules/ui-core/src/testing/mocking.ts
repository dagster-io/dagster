import {Unmasked} from '@apollo/client/masking';
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
          } as Unmasked<TQuery>)
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
          } as Unmasked<TMutation>)
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
let nativeOffsetHeight: PropertyDescriptor | undefined;
let nativeOffsetWidth: PropertyDescriptor | undefined;

/* simulate getBoundingClientRect returning a > 0x0 size, important for
testing React trees that useVirtualized().
Also mocks offsetHeight/offsetWidth which @tanstack/virtual-core v3 uses
(via getRect()) to measure scroll containers.
*/
export function mockViewportClientRect() {
  if (nativeGBRC) {
    return;
  }
  nativeGBRC = window.Element.prototype.getBoundingClientRect;
  window.Element.prototype.getBoundingClientRect = jest
    .fn()
    .mockReturnValue({height: 400, width: 400});

  nativeOffsetHeight = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'offsetHeight');
  nativeOffsetWidth = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'offsetWidth');
  Object.defineProperty(HTMLElement.prototype, 'offsetHeight', {
    configurable: true,
    get() {
      return 400;
    },
  });
  Object.defineProperty(HTMLElement.prototype, 'offsetWidth', {
    configurable: true,
    get() {
      return 400;
    },
  });
}

export function restoreViewportClientRect() {
  if (!nativeGBRC) {
    return;
  }
  window.Element.prototype.getBoundingClientRect = nativeGBRC;
  nativeGBRC = null;

  if (nativeOffsetHeight) {
    Object.defineProperty(HTMLElement.prototype, 'offsetHeight', nativeOffsetHeight);
  } else {
    Object.defineProperty(HTMLElement.prototype, 'offsetHeight', {
      configurable: true,
      get() {
        return 0;
      },
    });
  }
  if (nativeOffsetWidth) {
    Object.defineProperty(HTMLElement.prototype, 'offsetWidth', nativeOffsetWidth);
  } else {
    Object.defineProperty(HTMLElement.prototype, 'offsetWidth', {
      configurable: true,
      get() {
        return 0;
      },
    });
  }
  nativeOffsetHeight = undefined;
  nativeOffsetWidth = undefined;
}
