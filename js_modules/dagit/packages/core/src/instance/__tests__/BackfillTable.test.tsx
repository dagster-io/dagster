import {MockedProvider} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';
import {MemoryRouter} from 'react-router-dom';

import * as Alerting from '../../app/CustomAlertProvider';
import {BackfillTable} from '../BackfillTable';
import {
  BackfillTableFragmentFailedErrorStatus,
  BackfillTableFragmentFailedError,
} from '../__fixtures__/BackfillTable.fixtures';

// This file must be mocked because Jest can't handle `import.meta.url`.
jest.mock('../../graph/asyncGraphLayout', () => ({}));

describe('BackfillTable', () => {
  it('allows you to click "Failed" backfills for error details', async () => {
    jest.spyOn(Alerting, 'showCustomAlert');

    render(
      <MemoryRouter>
        <Alerting.CustomAlertProvider />
        <MockedProvider mocks={[BackfillTableFragmentFailedErrorStatus]}>
          <BackfillTable backfills={[BackfillTableFragmentFailedError]} refetch={() => {}} />
        </MockedProvider>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole('table')).toBeVisible();
      const statusLabel = screen.getByText('Failed');
      statusLabel.click();
      expect(Alerting.showCustomAlert).toHaveBeenCalled();
    });
  });
});
