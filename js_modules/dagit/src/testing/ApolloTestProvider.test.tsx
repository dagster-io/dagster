import {useQuery} from '@apollo/client';
import {render, screen} from '@testing-library/react';
import React from 'react';

import {INSTANCE_DETAIL_SUMMARY_QUERY} from 'src/nav/InstanceDetailsLink';
import {InstanceDetailSummaryQuery} from 'src/nav/types/InstanceDetailSummaryQuery';
import {ApolloTestProvider} from 'src/testing/ApolloTestProvider';

describe('ApolloTestProvider', () => {
  const Thing = () => {
    const {data} = useQuery<InstanceDetailSummaryQuery>(INSTANCE_DETAIL_SUMMARY_QUERY, {
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
