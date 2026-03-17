import {MockedProvider} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter} from 'react-router-dom';

import {
  getMockResultFn,
  mockViewportClientRect,
  restoreViewportClientRect,
} from '../../../testing/mocking';
import {
  buildReportCheckPartitionDefinitionQueryMock,
  buildReportCheckPartitionHealthQueryMock,
  buildReportCheckPartitionedPartitionDefinitionQueryMock,
  buildReportCheckPassedMutationMock,
  testCheck,
  testCheckPartitioned,
} from '../__fixtures__/useReportCheckEvaluationDialog.fixtures';
import {useReportCheckEvaluationDialog} from '../useReportCheckEvaluationDialog';

const TestWrapper = ({check}: {check: typeof testCheck | typeof testCheckPartitioned}) => {
  const {setIsOpen, element} = useReportCheckEvaluationDialog(check);
  return (
    <>
      <button onClick={() => setIsOpen(true)}>Open dialog</button>
      {element}
    </>
  );
};

describe('useReportCheckEvaluationDialog', () => {
  describe('unpartitioned check', () => {
    it('renders evaluation result options and fires the mutation on submit', async () => {
      const mutationMock = buildReportCheckPassedMutationMock();
      const mutationResultFn = getMockResultFn(mutationMock);

      const user = userEvent.setup();
      render(
        <MemoryRouter>
          <MockedProvider mocks={[buildReportCheckPartitionDefinitionQueryMock(), mutationMock]}>
            <TestWrapper check={testCheck} />
          </MockedProvider>
        </MemoryRouter>,
      );

      await user.click(screen.getByText('Open dialog'));

      expect(await screen.findByText('Report check evaluation')).toBeVisible();

      // The three evaluation result radio options are all present
      expect(screen.getByText('Passed')).toBeVisible();
      expect(screen.getByText('Failed (Warning)')).toBeVisible();
      expect(screen.getByText('Failed (Error)')).toBeVisible();

      // The description field is present
      expect(screen.getByPlaceholderText('Add a description')).toBeInTheDocument();

      // "Passed" is selected by default, so submit button is enabled
      const submitButton = screen.getByRole('button', {name: 'Report evaluation'});
      expect(submitButton).not.toBeDisabled();

      await user.click(submitButton);

      await waitFor(() => {
        expect(mutationResultFn).toHaveBeenCalled();
      });
    });
  });

  describe('partitioned check', () => {
    beforeAll(() => mockViewportClientRect());
    afterAll(() => restoreViewportClientRect());

    it('renders the partition section and disables submit when no partitions are selected', async () => {
      const user = userEvent.setup();
      render(
        <MemoryRouter>
          <MockedProvider
            mocks={[
              buildReportCheckPartitionedPartitionDefinitionQueryMock(),
              buildReportCheckPartitionHealthQueryMock(),
            ]}
          >
            <TestWrapper check={testCheckPartitioned} />
          </MockedProvider>
        </MemoryRouter>,
      );

      await user.click(screen.getByText('Open dialog'));

      expect(await screen.findByText('Report check evaluations')).toBeVisible();

      // Partition section is shown
      expect(screen.getByText('Partition selection')).toBeVisible();

      // Submit is disabled until partitions are selected
      const submitButton = screen.getByRole('button', {name: 'Report evaluation'});
      expect(submitButton).toBeDisabled();
    });
  });
});
