import {render, screen, waitFor} from '@testing-library/react';
import {BrowserRouter} from 'react-router-dom';

import {RunRequestTable} from '../DryRunRequestTable';
import {runRequests} from '../__fixtures__/SensorDryRunDialog.fixtures';

jest.mock('../../workspace/WorkspaceContext/util', () => ({
  ...jest.requireActual('../../workspace/WorkspaceContext/util'),
  useRepository: jest.fn(() => null),
}));

jest.mock('../../runs/RunConfigDialog', () => ({
  RunConfigDialog: () => <div>RunConfigDialog</div>,
}));

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
    render(<TestComponent />);

    runRequests.forEach((req) => {
      expect(screen.getByTestId(req.runKey!)).toBeVisible();
    });
  });

  it('renders preview button and opens dialog on click', async () => {
    render(<TestComponent />);

    const previewButton = screen.getByTestId(`preview-${runRequests[0]!.runKey || ''}`);
    expect(previewButton).toBeVisible();
    previewButton.click();

    await waitFor(() => {
      expect(screen.getByText(/RunConfigDialog/i)).toBeVisible();
    });
  });
});
