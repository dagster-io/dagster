import {act, render, screen} from '@testing-library/react';
import * as React from 'react';
import {BrowserRouter} from 'react-router-dom';

import {RunRequestTable} from '../DryRunRequestTable';
import {mockRepository} from '../__fixtures__/DryRunRequestTable.fixtures';
import {runRequests} from '../__fixtures__/SensorDryRunDialog.fixtures';

jest.mock('../../workspace/WorkspaceContext', () => ({useRepository: () => mockRepository}));

function TestComponent() {
  return (
    <BrowserRouter>
      <RunRequestTable
        name="test"
        repoAddress={{
          name: 'toys_repository',
          location: 'dagster_test.toys.repo',
        }}
        isJob={true}
        jobName="testJobName"
        runRequests={runRequests}
      />
    </BrowserRouter>
  );
}

describe('RunRequestTableTest', () => {
  it('renders results', async () => {
    await act(async () => {
      await render(<TestComponent />);
    });

    runRequests.forEach((req) => {
      req.tags.forEach(({key, value}) => {
        expect(screen.getByText(`${key}: ${value}`)).toBeVisible();
      });
      expect(screen.getByTestId(req.runKey!)).toBeVisible();
    });
  });
});
