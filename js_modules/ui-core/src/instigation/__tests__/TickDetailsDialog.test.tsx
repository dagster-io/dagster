import {render, screen} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';

import {buildInstigationSelector, buildInstigationTick} from '../../graphql/builders';
import {InstigationTickStatus} from '../../graphql/types';
import {TickDetailSummary, TickRequestedJobRunsTable} from '../TickDetailsDialog';

describe('TickRequestedJobRunsTable', () => {
  it('renders one row per job with partition keys and job page links', () => {
    render(
      <MemoryRouter>
        <TickRequestedJobRunsTable
          requestedRunsForJobs={[
            {jobName: 'partitioned_job', partitionKeys: ['p1', 'p2']},
            {jobName: 'unpartitioned_job', partitionKeys: []},
          ]}
          instigationSelector={buildInstigationSelector({
            repositoryName: 'foo',
            repositoryLocationName: 'bar',
          })}
        />
      </MemoryRouter>,
    );

    const partitionedLink = screen.getByRole('link', {name: 'partitioned_job'});
    expect(partitionedLink).toHaveAttribute(
      'href',
      expect.stringContaining('/jobs/partitioned_job'),
    );
    expect(screen.getByText('p1, p2')).toBeVisible();

    const unpartitionedLink = screen.getByRole('link', {name: 'unpartitioned_job'});
    expect(unpartitionedLink).toHaveAttribute(
      'href',
      expect.stringContaining('/jobs/unpartitioned_job'),
    );
    expect(screen.getByText('—')).toBeVisible();
  });
});

describe('TickDetailSummary', () => {
  it('includes job runs in the requested count for automation ticks', () => {
    const tick = buildInstigationTick({
      status: InstigationTickStatus.SUCCESS,
      requestedAssetMaterializationCount: 2,
      requestedJobRunCount: 1,
      runIds: [],
      error: null,
    });

    render(
      <MemoryRouter>
        <TickDetailSummary tick={tick} tickResultType="materializations" />
      </MemoryRouter>,
    );

    expect(screen.getByText(/3 requested/)).toBeVisible();
  });
});
