import {Toaster} from '@dagster-io/ui-components';
import {render, screen, within} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter} from 'react-router-dom';

import {DagsterTag} from '../../RunTag';
import {RunTagsDialog} from '../RunTagsDialog';
import {runEntry, tag} from '../__fixtures__/RunsFeedEntries.fixtures';
import {MappedRun} from '../mapRunsFeedData';

const renderDialog = (run: MappedRun) =>
  render(
    <MemoryRouter>
      <Toaster />
      <RunTagsDialog run={run} onClose={() => {}} />
    </MemoryRouter>,
  );

const DEFAULT_TAGS = [
  tag('team', 'data'),
  tag(DagsterTag.Partition, '2026-09-08'),
  tag('env', 'prod: east'),
];

const buildTaggedRun = (tags = DEFAULT_TAGS) =>
  runEntry({
    id: 'a1b2c3d4-1111-2222-3333-444455556666',
    tags,
  });

const findRow = async (key: string) =>
  within(await screen.findByRole('row', {name: new RegExp(`^${key} `)}));

describe('RunTagsDialog', () => {
  it('lists the tags sorted by key with the partition and run ID in the header', async () => {
    renderDialog(buildTaggedRun());

    const [, ...rows] = await screen.findAllByRole('row');
    expect(rows.map((row) => within(row).getAllByRole('cell')[0]?.textContent)).toEqual([
      'dagster/partition',
      'env',
      'team',
    ]);
    expect(await screen.findByText('data')).toBeVisible();
    expect(await screen.findAllByText('2026-09-08')).toHaveLength(2);
    expect(await screen.findByRole('link', {name: 'Run a1b2c3d4'})).toBeVisible();
  });

  it('copies one tag as key and value', async () => {
    const user = userEvent.setup();
    renderDialog(buildTaggedRun());

    const row = await findRow('env');
    await user.click(await row.findByRole('button', {name: 'Copy tag'}));

    expect(await screen.findByText('Tag copied')).toBeVisible();
    expect(await navigator.clipboard.readText()).toBe('env: prod: east');
  });

  it('copies every tag as YAML with Copy all', async () => {
    const user = userEvent.setup();
    renderDialog(buildTaggedRun());

    await user.click(await screen.findByRole('button', {name: /Copy all$/}));

    expect(await screen.findByText('All tags copied')).toBeVisible();
    expect(await navigator.clipboard.readText()).toBe(
      'dagster/partition: 2026-09-08\nenv: "prod: east"\nteam: data\n',
    );
  });
});
