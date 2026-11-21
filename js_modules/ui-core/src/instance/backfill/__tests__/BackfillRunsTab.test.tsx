import {MockedProvider} from '@apollo/client/testing';
import {render, waitFor} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';

import {buildPartitionBackfill} from '../../../graphql/builders';
import {DagsterTag} from '../../../runs/RunTag';
import {RunsFeedTableWithFilters} from '../../../runs/RunsFeedTable';
import {BackfillRunsTab} from '../BackfillRunsTab';

jest.mock('../../../runs/RunsFeedTable', () => ({
  RunsFeedTableWithFilters: jest.fn(() => null),
}));

describe('BackfillRunsTab', () => {
  it('keeps the same filter across renders while the search is unchanged', async () => {
    const backfill = buildPartitionBackfill({id: 'this_backfill'});
    const renderTab = () => (
      <MockedProvider>
        <MemoryRouter initialEntries={[`/backfill?q[]=${encodeURIComponent('tag:team=data')}`]}>
          <BackfillRunsTab backfill={backfill} view="list" />
        </MemoryRouter>
      </MockedProvider>
    );

    const {rerender} = render(renderTab());
    await waitFor(() => {
      expect(RunsFeedTableWithFilters).toHaveBeenCalled();
    });
    const firstFilter = jest.mocked(RunsFeedTableWithFilters).mock.lastCall?.[0].filter;
    expect(firstFilter).toEqual({
      tags: [
        {key: 'team', value: 'data'},
        {key: DagsterTag.Backfill, value: backfill.id},
      ],
    });

    rerender(renderTab());

    const {calls} = jest.mocked(RunsFeedTableWithFilters).mock;
    expect(calls.length).toBeGreaterThan(1);
    expect(calls.at(-1)?.[0].filter).toBe(firstFilter);
  });
});
