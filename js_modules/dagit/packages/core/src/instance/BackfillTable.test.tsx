import {MockedProvider} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';

import * as Alerting from '../app/CustomAlertProvider';
import {TestProvider} from '../testing/TestProvider';

import {BackfillTable} from './BackfillTable';
import {
  BackfillTableFragmentFailedErrorStatus,
  BackfillTableFragmentFailedError,
} from './BackfillTable.mocks';

// This file must be mocked because Jest can't handle `import.meta.url`.
jest.mock('../graph/asyncGraphLayout', () => ({}));

describe('BackfillTable', () => {
  it('allows you to click "Failed" backfills for error details', async () => {
    jest.spyOn(Alerting, 'showCustomAlert');

    render(
      <TestProvider>
        <Alerting.CustomAlertProvider />
        <MockedProvider mocks={[BackfillTableFragmentFailedErrorStatus]}>
          <BackfillTable backfills={[BackfillTableFragmentFailedError]} refetch={() => {}} />
        </MockedProvider>
      </TestProvider>,
    );

    await waitFor(() => {
      expect(screen.getByRole('table')).toBeVisible();
      const statusLabel = screen.getByText('Failed');
      statusLabel.click();
      expect(Alerting.showCustomAlert).toHaveBeenCalled();
    });
  });
});
