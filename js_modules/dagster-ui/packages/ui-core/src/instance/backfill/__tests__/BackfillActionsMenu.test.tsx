import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {CustomTooltipProvider} from '@dagster-io/ui-components';
import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {act} from 'react';
import {MemoryRouter} from 'react-router-dom';

import {ReexecutionParams, ReexecutionStrategy} from '../../../graphql/types';
import {BackfillActionsMenu} from '../BackfillActionsMenu';
import {
  BackfillTableFragmentCompletedAssetJob,
  BackfillTableFragmentFailedError,
  BackfillTableFragmentRequested2000AssetsPure,
} from '../__fixtures__/BackfillTable.fixtures';
import {
  ReexecuteBackfillMutation,
  ReexecuteBackfillMutationVariables,
} from '../types/useReexecuteBackfill.types';
import {REEXECUTE_BACKFILL_MUTATION} from '../useReexecuteBackfill';

describe('BackfillActionsMenu', () => {
  it('enables re-execute and "re-execute from failure" for failed backfills and they trigger the mutations', async () => {
    const user = userEvent.setup();

    const reexecuteMock = buildReexecuteMock({
      parentRunId: BackfillTableFragmentFailedError.id,
      strategy: ReexecutionStrategy.ALL_STEPS,
    });

    const reexecuteFromFailureMock = buildReexecuteMock({
      parentRunId: BackfillTableFragmentFailedError.id,
      strategy: ReexecutionStrategy.FROM_FAILURE,
    });

    await act(async () => {
      render(
        <MemoryRouter>
          <CustomTooltipProvider />
          <MockedProvider mocks={[reexecuteMock, reexecuteFromFailureMock]}>
            <BackfillActionsMenu backfill={BackfillTableFragmentFailedError} refetch={() => {}} />
          </MockedProvider>
        </MemoryRouter>,
      );
    });

    const dropdown = await screen.findByTestId('backfill_actions_dropdown_toggle');
    await user.click(dropdown);

    const reexecute = screen.getByText('Re-execute');
    expectAriaEnabled(reexecute.parentElement, true);
    await user.click(reexecute);
    await waitFor(() => expect(reexecuteMock.result).toHaveBeenCalled());

    const reexecuteFromFailure = screen.getByText('Re-execute from failure');
    expectAriaEnabled(reexecuteFromFailure.parentElement, true);
    await user.click(reexecuteFromFailure);
    await waitFor(() => expect(reexecuteFromFailureMock.result).toHaveBeenCalled());

    // Disabled on failed backfills
    const cancel = screen.getByText('Cancel backfill');
    expectAriaEnabled(cancel.parentElement, false);
  });

  it('does not enable re-execute and "re-execute from failure" for in-progress backfills', async () => {
    const user = userEvent.setup();

    await act(async () => {
      render(
        <MemoryRouter>
          <CustomTooltipProvider />
          <MockedProvider mocks={[]}>
            <BackfillActionsMenu
              backfill={BackfillTableFragmentRequested2000AssetsPure}
              refetch={() => {}}
            />
          </MockedProvider>
        </MemoryRouter>,
      );
    });

    const dropdown = await screen.findByTestId('backfill_actions_dropdown_toggle');
    expect(dropdown).toBeVisible();
    await user.click(dropdown);

    const reexecute = screen.getByText('Re-execute');
    expectAriaEnabled(reexecute.parentElement, false);
    const reexecuteFromFailure = screen.getByText('Re-execute from failure');
    expectAriaEnabled(reexecuteFromFailure.parentElement, false);
    const cancel = screen.getByText('Cancel backfill');
    expectAriaEnabled(cancel.parentElement, true);
  });

  it('enables re-execute for successful backfills and disables "re-execute from failure"', async () => {
    const user = userEvent.setup();

    await act(async () => {
      render(
        <MemoryRouter>
          <CustomTooltipProvider />
          <MockedProvider mocks={[]}>
            <BackfillActionsMenu
              backfill={BackfillTableFragmentCompletedAssetJob}
              refetch={() => {}}
            />
          </MockedProvider>
        </MemoryRouter>,
      );
    });

    const dropdown = await screen.findByTestId('backfill_actions_dropdown_toggle');
    expect(dropdown).toBeVisible();
    await user.click(dropdown);

    const reexecute = screen.getByText('Re-execute');
    expectAriaEnabled(reexecute.parentElement, true);
    const reexecuteFromFailure = screen.getByText('Re-execute from failure');
    expectAriaEnabled(reexecuteFromFailure.parentElement, false);
    const cancel = screen.getByText('Cancel backfill');
    expectAriaEnabled(cancel.parentElement, false);
  });
});

function buildReexecuteMock(
  reexecutionParams: ReexecutionParams,
): MockedResponse<ReexecuteBackfillMutation, ReexecuteBackfillMutationVariables> {
  return {
    request: {
      query: REEXECUTE_BACKFILL_MUTATION,
      variables: {reexecutionParams},
    },
    result: jest.fn(() => ({
      data: {
        __typename: 'Mutation',
        reexecutePartitionBackfill: {__typename: 'LaunchBackfillSuccess', backfillId: 'backfillid'},
      },
    })),
  };
}

const expectAriaEnabled = (e: HTMLElement | null, enabled: boolean) =>
  enabled
    ? expect(e).not.toHaveAttribute('aria-disabled', 'true')
    : expect(e).toHaveAttribute('aria-disabled', 'true');
