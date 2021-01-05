import {useQuery} from '@apollo/client';
import {render, screen} from '@testing-library/react';
import React from 'react';

import {INSTANCE_CONFIG_QUERY} from 'src/instance/InstanceConfig';
import {InstanceConfigQuery} from 'src/instance/types/InstanceConfigQuery';
import {ApolloTestProvider} from 'src/testing/ApolloTestProvider';

describe('ApolloTestProvider', () => {
  const Thing = () => {
    const {data} = useQuery<InstanceConfigQuery>(INSTANCE_CONFIG_QUERY, {
      fetchPolicy: 'cache-and-network',
    });
    return (
      <>
        <div>Version: {data?.version || ''}</div>
        <div>Info: {data?.instance.info || ''}</div>
      </>
    );
  };

  it('successfully mocks values', async () => {
    render(
      <ApolloTestProvider>
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
      <ApolloTestProvider mocks={mocks}>
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
      <ApolloTestProvider mocks={mocks}>
        <Thing />
      </ApolloTestProvider>,
    );
    const result = await screen.findAllByText('Info: just some info');
    expect(result.length).toBe(1);
  });
});
