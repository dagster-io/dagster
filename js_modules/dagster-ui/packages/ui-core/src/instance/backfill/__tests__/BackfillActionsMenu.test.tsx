import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {CustomTooltipProvider} from '@dagster-io/ui-components';
import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter} from 'react-router-dom';

import {
  ReexecutionParams,
  ReexecutionStrategy,
  buildLaunchBackfillSuccess,
  buildMutation,
} from '../../../graphql/types';
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

    render(
      <MemoryRouter>
        <CustomTooltipProvider />
        <MockedProvider mocks={[reexecuteMock, reexecuteFromFailureMock]}>
          <BackfillActionsMenu backfill={BackfillTableFragmentFailedError} refetch={() => {}} />
        </MockedProvider>
      </MemoryRouter>,
    );

    const dropdown = await screen.findByTestId('backfill_actions_dropdown_toggle');
    await user.click(dropdown);

    const reexecute = await screen.findByRole('menuitem', {name: /re-execute$/i});
    expect(reexecute).toBeEnabled();

    await user.click(reexecute);
    await waitFor(() => expect(reexecuteMock.result).toHaveBeenCalled());

    const reexecuteFromFailure = await screen.findByRole('menuitem', {
      name: /re-execute from failure$/i,
    });
    expect(reexecuteFromFailure).toBeEnabled();

    await user.click(reexecuteFromFailure);
    await waitFor(() => expect(reexecuteFromFailureMock.result).toHaveBeenCalled());

    // Disabled on failed backfills
    const cancel = await screen.findByRole('menuitem', {name: /cancel backfill$/i});
    expect(cancel).toBeDisabled();
  });

  it('does not enable re-execute and "re-execute from failure" for in-progress backfills', async () => {
    const user = userEvent.setup();

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

    const dropdown = await screen.findByTestId('backfill_actions_dropdown_toggle');
    expect(dropdown).toBeVisible();
    await user.click(dropdown);

    const reexecute = await screen.findByRole('menuitem', {name: /re-execute$/i});
    expect(reexecute).toBeDisabled();
    const reexecuteFromFailure = await screen.findByRole('menuitem', {
      name: /re-execute from failure$/i,
    });
    expect(reexecuteFromFailure).toBeDisabled();
    const cancel = await screen.findByRole('menuitem', {name: /cancel backfill$/i});
    expect(cancel).toBeEnabled();
  });

  it('enables re-execute for successful backfills and disables "re-execute from failure"', async () => {
    const user = userEvent.setup();

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

    const dropdown = await screen.findByTestId('backfill_actions_dropdown_toggle');
    expect(dropdown).toBeVisible();
    await user.click(dropdown);

    const reexecute = await screen.findByRole('menuitem', {name: /re\-execute$/i});
    expect(reexecute).toBeEnabled();
    const reexecuteFromFailure = await screen.findByRole('menuitem', {
      name: /re\-execute from failure$/i,
    });
    expect(reexecuteFromFailure).toBeDisabled();
    const cancel = await screen.findByRole('menuitem', {name: /cancel backfill$/i});
    expect(cancel).toBeDisabled();
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
      data: buildMutation({
        reexecutePartitionBackfill: buildLaunchBackfillSuccess({backfillId: 'backfillid'}),
      }),
    })),
  };
}
