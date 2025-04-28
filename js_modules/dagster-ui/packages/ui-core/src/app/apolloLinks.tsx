import {ApolloLink} from '../apollo-client';

const getCalls = (response: any) => {
  try {
    return JSON.parse(response.headers.get('x-dagster-call-counts'));
  } catch {
    return null;
  }
};

export const logLink = new ApolloLink((operation, forward) =>
  forward(operation).map((data) => {
    const context = operation.getContext();
    const elapsedTime = performance.now() - context.start;
    const calls = getCalls(context.response);
    operation.setContext({elapsedTime, calls});
    return data;
  }),
);

export const timeStartLink = new ApolloLink((operation, forward) => {
  operation.setContext({start: performance.now()});
  return forward(operation);
});
