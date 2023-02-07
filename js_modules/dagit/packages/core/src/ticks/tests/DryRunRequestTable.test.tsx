import {Resolvers} from '@apollo/client';
import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {act, getByText, queryAllByRole, render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';
import {BrowserRouter, Router} from 'react-router-dom';

import {RunRequest} from '../../graphql/types';
import {TestProvider} from '../../testing/TestProvider';
import {RunRequestTable} from '../DryRunRequestTable';

import {mockRepository} from './DryRunRequestTable.mocks';
import {SensorDryRunMutationRunRequests} from './SensorDryRun.mocks';

jest.mock('../../workspace/WorkspaceContext', () => ({useRepository: () => mockRepository}));

// Not sure how to better handle this. Since we typed our mock with MockedResponse typescript thinks
// these fields are nullable but they're not.
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
const runRequests = SensorDryRunMutationRunRequests!.result!.data.sensorDryRun.evaluationResult
  .runRequests as RunRequest[];

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
      expect(screen.getByTestId(req.runKey)).toBeVisible();
    });
  });
});
