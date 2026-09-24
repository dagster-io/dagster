import {render, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter} from 'react-router-dom';

import {RunIDCell} from '../RunIDCell';
import {backfillEntry, runEntry} from '../__fixtures__/RunsFeedEntries.fixtures';
import {MappedRunsFeedEntry} from '../mapRunsFeedData';

const RUN_ID = 'a1b2c3d4-1111-2222-3333-444455556666';
const BACKFILL_ID = 'bkfl1234';

const renderCell = (entry: MappedRunsFeedEntry) =>
  render(
    <MemoryRouter>
      <RunIDCell entry={entry} />
    </MemoryRouter>,
  );

describe('RunIDCell', () => {
  it('links the leading characters of a run id to the run', async () => {
    renderCell(runEntry({id: RUN_ID}));
    const link = await screen.findByRole('link', {name: 'Run a1b2c3d4'});
    expect(link).toHaveAttribute('href', `/runs/${RUN_ID}`);
    expect(link).toHaveTextContent('a1b2c3d4');
  });

  it('links a short backfill id to its backfill page', async () => {
    renderCell(backfillEntry({id: BACKFILL_ID}));
    const link = await screen.findByRole('link', {name: 'Backfill bkfl1234'});
    expect(link).toHaveAttribute('href', `/runs/b/${BACKFILL_ID}`);
    expect(link).toHaveTextContent(BACKFILL_ID);
  });

  it('reveals the full id on hover', async () => {
    const user = userEvent.setup();
    renderCell(runEntry({id: RUN_ID}));

    await user.hover(await screen.findByRole('link', {name: 'Run a1b2c3d4'}));
    expect(await screen.findByRole('tooltip')).toHaveTextContent(RUN_ID);
  });
});
