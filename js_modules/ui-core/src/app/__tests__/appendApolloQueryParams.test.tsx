import {appendApolloQueryParams} from '../appendApolloQueryParams';

describe('appendApolloQueryParams', () => {
  it('uri has origin: append query params to a URI', () => {
    expect(appendApolloQueryParams('http://localhost:8000/graphql', {op: 'foo'})).toEqual(
      'http://localhost:8000/graphql?op=foo',
    );
    expect(
      appendApolloQueryParams('http://localhost:8000/graphql?lorem=ipsum', {op: 'foo'}),
    ).toEqual('http://localhost:8000/graphql?lorem=ipsum&op=foo');
  });

  it('uri does not have origin: return path and query params', () => {
    expect(appendApolloQueryParams('/graphql', {op: 'foo'})).toEqual('/graphql?op=foo');
    expect(appendApolloQueryParams('/graphql?lorem=ipsum', {op: 'foo'})).toEqual(
      '/graphql?lorem=ipsum&op=foo',
    );
  });
});
