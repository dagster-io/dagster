import {MockedProvider} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter} from 'react-router-dom';

import {buildInstigationState, buildInstigationTick} from '../../../graphql/builders';
import {InstigationTickStatus, InstigationType} from '../../../graphql/types';
import {JOB_SELECTED_TICK_QUERY} from '../../../instigation/TickDetailsDialog';
import {
  SelectedTickQuery,
  SelectedTickQueryVariables,
} from '../../../instigation/types/TickDetailsDialog.types';
import {buildQueryMock} from '../../../testing/mocking';
import {DagsterTag} from '../../RunTag';
import {RunsFeedList} from '../RunsFeedList';
import {
  FIXTURE_NOW_MS,
  backfillEntry,
  runEntry,
  tag,
} from '../__fixtures__/RunsFeedEntries.fixtures';
import {MappedRunsFeedEntry} from '../mapRunsFeedData';

const HOURLY_RUN_ID = 'a1b2c3d4-1111-2222-3333-444455556666';
const NIGHTLY_RUN_ID = 'bbbbbbbb-1111-2222-3333-444455556666';
const BACKFILL_ID = 'bkfl1234';

const TICK_DIALOG_HEADING = 'Requested materializations';

const hourlyRun = runEntry({
  id: HOURLY_RUN_ID,
  tags: [tag(DagsterTag.ScheduleName, 'hourly_schedule'), tag(DagsterTag.TickId, 'tick-id')],
});

const nightlyRun = runEntry({
  id: NIGHTLY_RUN_ID,
  tags: [tag(DagsterTag.ScheduleName, 'nightly_schedule'), tag(DagsterTag.TickId, 'tick-2')],
});

const completedBackfill = backfillEntry({id: BACKFILL_ID});

const buildTickMock = (scheduleName: string, tickId: string) =>
  buildQueryMock<SelectedTickQuery, SelectedTickQueryVariables>({
    query: JOB_SELECTED_TICK_QUERY,
    variables: {
      instigationSelector: {
        name: scheduleName,
        repositoryName: 'my_repo',
        repositoryLocationName: 'my_location',
      },
      tickId,
    },
    data: {
      instigationStateOrError: buildInstigationState({
        id: `${scheduleName}-state-id`,
        tick: buildInstigationTick({
          id: tickId,
          tickId,
          instigationType: InstigationType.SCHEDULE,
          status: InstigationTickStatus.SUCCESS,
          timestamp: FIXTURE_NOW_MS / 1000 - 600,
          requestedAssetMaterializationCount: 3,
          requestedJobRunCount: 0,
          error: null,
          skipReason: null,
        }),
      }),
    },
    maxUsageCount: Number.POSITIVE_INFINITY,
  });

type ListProps = {
  entries: MappedRunsFeedEntry[];
  isLoading?: boolean;
};

const renderList = ({entries, isLoading = false}: ListProps) => {
  const wrap = ({entries: nextEntries, isLoading: nextIsLoading = false}: ListProps) => (
    <MemoryRouter>
      <MockedProvider
        mocks={[
          buildTickMock('hourly_schedule', 'tick-id'),
          buildTickMock('nightly_schedule', 'tick-2'),
        ]}
      >
        <RunsFeedList entries={nextEntries} isLoading={nextIsLoading} />
      </MockedProvider>
    </MemoryRouter>
  );

  const {container, rerender} = render(wrap({entries, isLoading}));
  return {
    list: container.querySelector('[aria-busy]'),
    rerenderList: (next: ListProps) => rerender(wrap(next)),
  };
};

const findTickButton = async (position: number) => {
  const buttons = await screen.findAllByRole('button', {name: 'View tick'});
  const button = buttons[position];
  if (button === undefined) {
    throw new Error(`No "View tick" button in position ${position}`);
  }
  return button;
};

const findIdLinks = () => screen.findAllByRole('link', {name: /^(Run|Backfill) /});

describe('RunsFeedList', () => {
  it('renders a row for each entry, in order', async () => {
    const {list} = renderList({entries: [hourlyRun, nightlyRun, completedBackfill]});

    const idLinks = await findIdLinks();
    expect(idLinks.map((link) => link.getAttribute('href'))).toEqual([
      `/runs/${HOURLY_RUN_ID}`,
      `/runs/${NIGHTLY_RUN_ID}`,
      `/runs/b/${BACKFILL_ID}`,
    ]);
    expect(list).toHaveAttribute('aria-busy', 'false');
  });

  it('reports a busy list while the first page loads', async () => {
    const {list} = renderList({entries: [], isLoading: true});

    expect(await screen.findByRole('status')).toHaveTextContent('Loading runs');
    expect(list).toHaveAttribute('aria-busy', 'true');
  });

  it('keeps the rows while a refresh is in flight', async () => {
    const {list} = renderList({entries: [hourlyRun], isLoading: true});

    expect(await findIdLinks()).toHaveLength(1);
    expect(list).toHaveAttribute('aria-busy', 'true');
    expect(screen.getByRole('status')).toBeEmptyDOMElement();
  });

  it('opens the tick dialog from a row and returns focus to that row on close', async () => {
    const user = userEvent.setup();
    renderList({entries: [hourlyRun, nightlyRun]});

    const button = await findTickButton(0);
    await user.click(button);
    expect(await screen.findByText(TICK_DIALOG_HEADING)).toBeVisible();

    await user.click(await screen.findByRole('button', {name: 'Close'}));
    await waitFor(() => expect(button).toHaveFocus());
  });

  it('keeps the tick dialog open when its row leaves the list', async () => {
    const user = userEvent.setup();
    const {rerenderList} = renderList({entries: [hourlyRun, nightlyRun]});

    await user.click(await findTickButton(1));
    expect(await screen.findByText(TICK_DIALOG_HEADING)).toBeVisible();

    rerenderList({entries: [hourlyRun]});
    expect(screen.getByText(TICK_DIALOG_HEADING)).toBeVisible();

    await user.click(await screen.findByRole('button', {name: 'Close'}));
    const scheduleLink = await screen.findByRole('link', {name: /hourly_schedule/});
    await waitFor(() => expect(scheduleLink).toHaveFocus());
  });

  it('falls back to the list itself when no rows remain', async () => {
    const user = userEvent.setup();
    const {list, rerenderList} = renderList({entries: [hourlyRun]});

    await user.click(await findTickButton(0));
    expect(await screen.findByText(TICK_DIALOG_HEADING)).toBeVisible();

    rerenderList({entries: []});
    await user.click(await screen.findByRole('button', {name: 'Close'}));
    await waitFor(() => expect(list).toHaveFocus());
  });
});
