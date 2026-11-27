import {MockedProvider} from '@apollo/client/testing';
import {act, render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter} from 'react-router-dom';

import {ApolloLink, Observable} from '../../../apollo-client';
import * as Alerting from '../../../app/CustomAlertProvider';
import {BulkActionStatus} from '../../../graphql/types';
import {BackfillTable} from '../BackfillTable';
import {
  BackfillTableFragmentCompletedOpJob,
  BackfillTableFragmentFailedError,
} from '../__fixtures__/BackfillTable.fixtures';

// This file must be mocked because Jest can't handle `import.meta.url`.
jest.mock('../../../graph/asyncGraphLayout', () => ({}));

describe('BackfillTable', () => {
  it('renders and updates op backfill status without fetching runs or polling', async () => {
    jest.useFakeTimers();
    const request = jest.fn();
    const link = new ApolloLink(() => {
      request();
      return new Observable(() => {});
    });
    const backfill = {
      ...BackfillTableFragmentCompletedOpJob,
      isAssetBackfill: false,
      status: BulkActionStatus.REQUESTED,
    };
    const table = (status: BulkActionStatus) => (
      <MemoryRouter>
        <MockedProvider mocks={[]} link={link}>
          <BackfillTable backfills={[{...backfill, status}]} refetch={() => {}} />
        </MockedProvider>
      </MemoryRouter>
    );

    try {
      const {rerender, unmount} = render(table(BulkActionStatus.REQUESTED));
      expect(screen.getByText('In progress')).toBeVisible();

      // Pass both the old 100ms query delay and two 15-second refresh intervals.
      await act(async () => {
        jest.advanceTimersByTime(100);
      });
      await act(async () => {
        jest.advanceTimersByTime(30_000);
      });

      expect(request).not.toHaveBeenCalled();
      expect(screen.getByText('In progress')).toBeVisible();

      rerender(table(BulkActionStatus.COMPLETED_SUCCESS));
      expect(screen.getByText('Succeeded')).toBeVisible();
      expect(screen.queryByText('In progress')).not.toBeInTheDocument();
      unmount();
    } finally {
      jest.useRealTimers();
    }
  });

  it('allows you to click "Failed" backfills for error details', async () => {
    jest.spyOn(Alerting, 'showCustomAlert');
    const user = userEvent.setup();

    await act(async () => {
      await render(
        <MemoryRouter>
          <Alerting.CustomAlertProvider />
          <MockedProvider mocks={[]}>
            <BackfillTable backfills={[BackfillTableFragmentFailedError]} refetch={() => {}} />
          </MockedProvider>
        </MemoryRouter>,
      );
    });

    await waitFor(() => {
      expect(screen.getByRole('table')).toBeVisible();
    });
    const statusLabel = await screen.findByText('Failed');
    await user.click(statusLabel);
    await waitFor(() => {
      expect(Alerting.showCustomAlert).toHaveBeenCalled();
    });
  });
});
