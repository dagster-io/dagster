import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {render, screen} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';

import {buildAssetCheckhandle, buildAssetKey, buildRun} from '../../graphql/builders';
import {RUN_ASSETS_CHECKS_QUERY, RunAssetCheckTags} from '../RunAssetCheckTags';
import {RunAssetChecksQuery} from '../types/RunAssetCheckTags.types';

describe('RunAssetCheckTags', () => {
  const RUN_ID = 'abc';

  const makeChecks = (checkCount: number) =>
    Array(checkCount)
      .fill(null)
      .map((_, idx) =>
        buildAssetCheckhandle({
          name: `check_${idx}`,
          assetKey: buildAssetKey({path: [`asset_${idx}`]}),
        }),
      );

  const buildMock = (checkCount: number): MockedResponse<RunAssetChecksQuery> => ({
    request: {query: RUN_ASSETS_CHECKS_QUERY, variables: {runId: RUN_ID}},
    result: {
      data: {
        __typename: 'Query',
        pipelineRunOrError: buildRun({id: RUN_ID, assetChecks: makeChecks(checkCount)}),
      },
    },
  });

  // A null/empty selection means "every check on the targeted assets"; the targeted checks come
  // from the run's execution plan (via the resolver), so the query runs.
  it('renders a count tag from the resolved assetChecks query', async () => {
    render(
      <MockedProvider mocks={[buildMock(1221)]}>
        <MemoryRouter>
          <RunAssetCheckTags
            run={{id: RUN_ID, pipelineName: '__ASSET_JOB_0', assetCheckSelection: null}}
          />
        </MemoryRouter>
      </MockedProvider>,
    );

    expect(await screen.findByText('1,221 checks')).toBeVisible();
  });

  // A hidden asset group job with an explicit (non-empty) selection uses that selection directly
  // and skips the query - so no query mock is provided here.
  it('renders from assetCheckSelection without querying for a hidden asset group job', async () => {
    render(
      <MockedProvider mocks={[]}>
        <MemoryRouter>
          <RunAssetCheckTags
            run={{
              id: RUN_ID,
              pipelineName: '__ASSET_JOB_0',
              assetCheckSelection: makeChecks(1221),
            }}
          />
        </MemoryRouter>
      </MockedProvider>,
    );

    expect(await screen.findByText('1,221 checks')).toBeVisible();
  });

  it('renders an individual check tag when only one check is targeted', async () => {
    render(
      <MockedProvider mocks={[buildMock(1)]}>
        <MemoryRouter>
          <RunAssetCheckTags
            run={{id: RUN_ID, pipelineName: '__ASSET_JOB_0', assetCheckSelection: null}}
          />
        </MemoryRouter>
      </MockedProvider>,
    );

    expect(await screen.findByText('check_0 on asset_0')).toBeVisible();
  });
});
