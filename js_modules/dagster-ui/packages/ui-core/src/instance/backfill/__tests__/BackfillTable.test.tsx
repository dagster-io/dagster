import {MockedProvider} from '@apollo/client/testing';
import {render, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter} from 'react-router-dom';

import * as Alerting from '../../../app/CustomAlertProvider';
import {BackfillTable} from '../BackfillTable';
import {
  BackfillTableFragmentFailedError,
  BackfillTableFragmentFailedErrorStatus,
} from '../__fixtures__/BackfillTable.fixtures';

// This file must be mocked because Jest can't handle `import.meta.url`.
jest.mock('../../../graph/asyncGraphLayout', () => ({}));

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

    expect(screen.getByRole('table')).toBeVisible();
    const statusLabel = await screen.findByText('Failed');
    await userEvent.click(statusLabel);
    expect(Alerting.showCustomAlert).toHaveBeenCalled();
  });
});
