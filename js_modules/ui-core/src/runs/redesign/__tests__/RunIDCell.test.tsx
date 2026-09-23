import {render, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import {RunIDCell} from '../RunIDCell';
import {backfillEntry, runEntry} from '../__fixtures__/RunsFeedEntries.fixtures';

const RUN_ID = 'a1b2c3d4-1111-2222-3333-444455556666';

describe('RunIDCell', () => {
  it('shows the leading characters of the id', async () => {
    render(<RunIDCell entry={runEntry({id: RUN_ID})} />);
    expect(await screen.findByText('a1b2c3d4')).toBeVisible();
  });

  it('reveals the full id on hover', async () => {
    const user = userEvent.setup();
    render(<RunIDCell entry={runEntry({id: RUN_ID})} />);
    await user.hover(await screen.findByText('a1b2c3d4'));
    expect(await screen.findByRole('tooltip')).toHaveTextContent(RUN_ID);
  });

  it('shows a short id whole', async () => {
    render(<RunIDCell entry={backfillEntry({id: 'bkfl1234'})} />);
    expect(await screen.findByText('bkfl1234')).toBeVisible();
  });
});
