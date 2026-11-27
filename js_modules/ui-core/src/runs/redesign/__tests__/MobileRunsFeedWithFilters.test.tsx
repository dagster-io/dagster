import {MockedProvider} from '@apollo/client/testing';
import {render, screen} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';

import {InMemoryCache} from '../../../apollo-client';
import {buildRunsFeedConnection} from '../../../graphql/builders';
import possibleTypes from '../../../graphql/possibleTypes.generated.json';
import {RunsFeedView, RunsFilter} from '../../../graphql/types';
import {MobileRunsFeedWithFilters} from '../MobileRunsFeedWithFilters';
import {RUNS_FEED_QUERY} from '../RunsFeedQuery';
import {RunsFeedQuery, RunsFeedQueryVariables} from '../types/RunsFeedQuery.types';

const SENSOR_FILTER: RunsFilter = {tags: [{key: 'dagster/sensor_name', value: 'my_sensor'}]};

const emptyFeedMock = {
  request: {
    query: RUNS_FEED_QUERY,
    variables: {limit: 30, filter: SENSOR_FILTER, view: RunsFeedView.RUNS},
  } satisfies {query: typeof RUNS_FEED_QUERY; variables: RunsFeedQueryVariables},
  result: {
    data: {
      __typename: 'Query',
      runsFeedOrError: {...buildRunsFeedConnection({cursor: 'end', hasMore: false}), results: []},
    } satisfies RunsFeedQuery,
  },
};

describe('MobileRunsFeedWithFilters', () => {
  it('treats the embedding page filter as a filter in the empty state', async () => {
    render(
      <MemoryRouter>
        <MockedProvider mocks={[emptyFeedMock]} cache={new InMemoryCache({possibleTypes})}>
          <MobileRunsFeedWithFilters filter={SENSOR_FILTER} includeRunsFromBackfills />
        </MockedProvider>
      </MemoryRouter>,
    );

    expect(await screen.findByText('No matching runs')).toBeVisible();
    expect(screen.queryByText('You have not launched any runs yet.')).toBeNull();
  });
});
