import * as React from 'react';
import {MockedProvider} from '@apollo/client/testing';
import {render, screen} from '@testing-library/react';

import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {OpJobPartitionsViewContent} from '../OpJobPartitionsView';
import {buildOpJobPartitionSetFragmentWithError} from '../__fixtures__/OpJobPartitionsViewContent.fixtures';

jest.mock('../usePartitionStepQuery', () => ({
  usePartitionStepQuery: () => [],
}));

jest.mock('../JobBackfillsTable', () => ({
  JobBackfillsTable: () => <div />,
}));

// This file must be mocked because Jest can't handle `import.meta.url`.
jest.mock('../../graph/asyncGraphLayout', () => ({}));

describe('OpJobPartitionsViewContent', () => {
  it('does not error when partition statuses are in an error state', async () => {
    const fragment = buildOpJobPartitionSetFragmentWithError();
    render(
      <MockedProvider>
        <OpJobPartitionsViewContent
          partitionNames={['lorem', 'ipsum']}
          partitionSet={fragment}
          repoAddress={buildRepoAddress('foo', 'bar')}
        />
      </MockedProvider>,
    );

    expect(await screen.findByTitle(/click to view per\-step status/i)).toBeVisible();
  });
});
