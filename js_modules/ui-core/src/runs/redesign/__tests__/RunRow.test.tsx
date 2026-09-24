import {MockedProvider} from '@apollo/client/testing';
import {fireEvent, render, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter, useLocation} from 'react-router-dom';

import {buildAssetKey, buildRun, buildRunStatsSnapshot} from '../../../graphql/builders';
import {buildQueryMock} from '../../../testing/mocking';
import {testId} from '../../../testing/testId';
import {RUN_STATS_QUERY} from '../../RunStats';
import {DagsterTag} from '../../RunTag';
import {RunStatsQuery, RunStatsQueryVariables} from '../../types/RunStats.types';
import {RunRow} from '../RunRow';
import {FIXTURE_NOW_MS, runEntry, tag} from '../__fixtures__/RunsFeedEntries.fixtures';
import {MappedRunsFeedEntry} from '../mapRunsFeedData';

const RUN_ID = 'a1b2c3d4-1111-2222-3333-444455556666';

const RUN_PATH = `/runs/${RUN_ID}`;
const LIST_PATH = '/runs';

const RUN_ID_LINK_NAME = 'Run a1b2c3d4';

const succeededRun = runEntry({id: RUN_ID});

const scheduledRunWithTargets = runEntry({
  id: RUN_ID,
  jobName: 'daily_etl',
  tags: [tag(DagsterTag.ScheduleName, 'hourly_schedule'), tag(DagsterTag.TickId, 'tick-id')],
  assetSelectionPreview: [
    buildAssetKey({path: ['sales', 'daily']}),
    buildAssetKey({path: ['sales', 'hourly']}),
    buildAssetKey({path: ['sales', 'weekly']}),
  ],
  assetSelectionCount: 3,
});

const statsMock = buildQueryMock<RunStatsQuery, RunStatsQueryVariables>({
  query: RUN_STATS_QUERY,
  variables: {runId: RUN_ID},
  data: {
    pipelineRunOrError: buildRun({
      id: RUN_ID,
      stats: buildRunStatsSnapshot({
        stepsSucceeded: 4,
        stepsFailed: 0,
        materializations: 3,
        expectations: 0,
      }),
    }),
  },
});

const CurrentPath = () => {
  const {pathname} = useLocation();
  return <div data-testid={testId('path')}>{pathname}</div>;
};

// jsdom leaves window.open unimplemented and logs an error when it is called.
const windowOpen = jest.fn();

// The row is the first element rendered; neither the router nor the mock provider adds one.
const renderRow = async (entry: MappedRunsFeedEntry, onOpenTickDetails = jest.fn()) => {
  const {container} = render(
    <MemoryRouter initialEntries={[LIST_PATH]}>
      <MockedProvider mocks={[statsMock]}>
        <RunRow entry={entry} onOpenTickDetails={onOpenTickDetails} />
      </MockedProvider>
      <CurrentPath />
    </MemoryRouter>,
  );

  await screen.findByRole('link', {name: /^(Run|Backfill) /});
  const row = container.firstElementChild;
  if (!(row instanceof HTMLElement)) {
    throw new Error('RunRow rendered no element');
  }
  return row;
};

const getCurrentPath = () => screen.getByTestId('path').textContent;

describe('RunRow', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.setSystemTime(FIXTURE_NOW_MS);
    jest.spyOn(window, 'open').mockImplementation(windowOpen);
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.restoreAllMocks();
  });

  it('opens the run when the row itself is clicked', async () => {
    const user = userEvent.setup({advanceTimers: jest.advanceTimersByTime});
    const row = await renderRow(succeededRun);

    await user.click(row);
    expect(getCurrentPath()).toBe(RUN_PATH);
  });

  it('opens the run when the timing text is clicked', async () => {
    const user = userEvent.setup({advanceTimers: jest.advanceTimersByTime});
    await renderRow(succeededRun);

    await user.click(await screen.findByText('5m ago'));
    expect(getCurrentPath()).toBe(RUN_PATH);
  });

  it('follows a link inside a cell instead of opening the run', async () => {
    const user = userEvent.setup({advanceTimers: jest.advanceTimersByTime});
    await renderRow(scheduledRunWithTargets);

    await user.click(await screen.findByRole('link', {name: /hourly_schedule/}));
    expect(getCurrentPath()).toBe('/locations/my_repo@my_location/schedules/hourly_schedule');
  });

  it('opens tick details without opening the run', async () => {
    const user = userEvent.setup({advanceTimers: jest.advanceTimersByTime});
    const onOpenTickDetails = jest.fn();
    await renderRow(scheduledRunWithTargets, onOpenTickDetails);

    await user.click(await screen.findByRole('button', {name: 'View tick'}));

    expect(onOpenTickDetails).toHaveBeenCalledTimes(1);
    expect(getCurrentPath()).toBe(LIST_PATH);
  });

  it('ignores a click that ends a text selection', async () => {
    const row = await renderRow(succeededRun);
    const selection = document.getSelection();
    if (selection === null) {
      throw new Error('This environment has no document selection');
    }

    const range = document.createRange();
    range.selectNodeContents(await screen.findByText('5m ago'));
    selection.removeAllRanges();
    selection.addRange(range);
    expect(selection.toString()).toBe('5m ago');

    fireEvent.click(row);
    expect(getCurrentPath()).toBe(LIST_PATH);

    selection.removeAllRanges();
    fireEvent.click(row);
    expect(getCurrentPath()).toBe(RUN_PATH);
  });

  it('keeps a click inside the step statistics popover from opening the run', async () => {
    const user = userEvent.setup({advanceTimers: jest.advanceTimersByTime});
    await renderRow(succeededRun);

    await user.hover(await screen.findByRole('img', {name: 'Success'}));
    await user.click(await screen.findByText('Success'));

    expect(getCurrentPath()).toBe(LIST_PATH);
  });

  it('opens a new tab for a modified click on the row', async () => {
    const row = await renderRow(succeededRun);

    fireEvent.click(row, {metaKey: true});
    fireEvent.click(row, {ctrlKey: true});
    fireEvent.click(row, {shiftKey: true});

    expect(windowOpen.mock.calls).toEqual([
      [RUN_PATH, '_blank'],
      [RUN_PATH, '_blank'],
      [RUN_PATH, '_blank'],
    ]);
    expect(getCurrentPath()).toBe(LIST_PATH);
  });

  it('does nothing for an alt click on the row', async () => {
    const row = await renderRow(succeededRun);

    fireEvent.click(row, {altKey: true});

    expect(windowOpen).not.toHaveBeenCalled();
    expect(getCurrentPath()).toBe(LIST_PATH);
  });

  it('opens a new tab for a middle click on the row', async () => {
    const row = await renderRow(succeededRun);

    const auxClick = new MouseEvent('auxclick', {bubbles: true, cancelable: true, button: 1});
    fireEvent(row, auxClick);

    expect(auxClick.defaultPrevented).toBe(true);
    expect(windowOpen).toHaveBeenCalledWith(RUN_PATH, '_blank');
    expect(getCurrentPath()).toBe(LIST_PATH);
  });

  it('leaves a right click on the row to the context menu, modified or not', async () => {
    const row = await renderRow(succeededRun);

    for (const modifier of [{}, {shiftKey: true}, {metaKey: true}, {ctrlKey: true}]) {
      const auxClick = new MouseEvent('auxclick', {
        bubbles: true,
        cancelable: true,
        button: 2,
        ...modifier,
      });
      fireEvent(row, auxClick);
      expect(auxClick.defaultPrevented).toBe(false);
    }

    expect(windowOpen).not.toHaveBeenCalled();
    expect(getCurrentPath()).toBe(LIST_PATH);
  });

  it('puts the id link last in the tab order', async () => {
    const user = userEvent.setup({advanceTimers: jest.advanceTimersByTime});
    await renderRow(scheduledRunWithTargets);

    const stops = [
      await screen.findByRole('link', {name: /hourly_schedule/}),
      await screen.findByRole('button', {name: 'View tick'}),
      await screen.findByRole('link', {name: 'daily_etl'}),
      await screen.findByRole('link', {name: '3 assets'}),
      await screen.findByText('5m ago'),
      await screen.findByRole('link', {name: RUN_ID_LINK_NAME}),
    ];

    for (const stop of stops) {
      await user.tab();
      expect(document.activeElement).toBe(stop);
    }
  });
});
