import {useQuery} from '@apollo/client';
import {render, screen} from '@testing-library/react';
import {loader} from 'graphql.macro';
import React from 'react';

import {INSTANCE_CONFIG_QUERY} from '../../instance/InstanceConfig';
import {
  InstanceConfigQuery,
  InstanceConfigQueryVariables,
} from '../../instance/types/InstanceConfig.types';
import {ApolloTestProvider} from '../ApolloTestProvider';

const typeDefs = loader('../../graphql/schema.graphql');

describe('ApolloTestProvider', () => {
  const Thing = () => {
    const {data} = useQuery<InstanceConfigQuery, InstanceConfigQueryVariables>(
      INSTANCE_CONFIG_QUERY,
    );
    return (
      <>
        <div>Version: {data?.version || ''}</div>
        <div>Info: {data?.instance.info || ''}</div>
      </>
    );
  };

  it('successfully mocks values', async () => {
    render(
      <ApolloTestProvider typeDefs={typeDefs as any}>
        <Thing />
      </ApolloTestProvider>,
    );
    const result = await screen.findAllByText('Version: x.y.z');
    expect(result.length).toBe(1);
  });

  it('allows overriding with mocked `Query` values', async () => {
    const mocks = {
      Query: () => ({
        version: () => '1234',
      }),
    };

    render(
      <ApolloTestProvider mocks={mocks} typeDefs={typeDefs as any}>
        <Thing />
      </ApolloTestProvider>,
    );
    const result = await screen.findAllByText('Version: 1234');
    expect(result.length).toBe(1);
  });

  it('allows overriding with mocked values on other types', async () => {
    const mocks = {
      Instance: () => ({
        info: () => 'just some info',
      }),
    };

    render(
      <ApolloTestProvider mocks={mocks} typeDefs={typeDefs as any}>
        <Thing />
      </ApolloTestProvider>,
    );
    const result = await screen.findAllByText('Info: just some info');
    expect(result.length).toBe(1);
  });
});
