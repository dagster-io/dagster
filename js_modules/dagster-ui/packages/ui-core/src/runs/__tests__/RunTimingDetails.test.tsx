import * as React from 'react';
import {render, screen} from '@testing-library/react';

import {TimeProvider} from '../../app/time/TimeContext';
import {RunStatus, buildRun} from '../../graphql/types';
import {RunTimingDetails} from '../RunTimingDetails';

jest.mock('../../app/time/browserTimezone.ts', () => ({
  browserTimezone: () => 'America/Los_Angeles',
}));

describe('RunTimingDetails', () => {
  const START_TIME = 1613571870.934;
  const END_TIME = 1613571916.945;
  const FAKE_NOW = 1613571931.945; // Fifteen seconds later

  let dateNow: any = null;
  beforeEach(() => {
    jest.useFakeTimers();
    dateNow = global.Date.now;
    const dateNowStub = jest.fn(() => FAKE_NOW * 1000);
    global.Date.now = dateNowStub;
  });

  afterEach(() => {
    jest.useRealTimers();
    global.Date.now = dateNow;
  });

  it('renders QUEUED details', async () => {
    const run = buildRun({
      id: 'abc',
      status: RunStatus.QUEUED,
      startTime: null,
      endTime: null,
    });

    render(
      <TimeProvider>
        <RunTimingDetails loading={false} run={run} />
      </TimeProvider>,
    );

    await screen.findByRole('table');

    const rows = screen.getAllByRole('row');
    expect(rows).toHaveLength(3);

    expect(screen.getByRole('row', {name: /started queued/i})).toBeVisible();
    expect(screen.getByRole('row', {name: /ended queued/i})).toBeVisible();
    expect(screen.getByRole('row', {name: /duration queued/i})).toBeVisible();
  });

  it('renders CANCELED details with start time', async () => {
    const run = buildRun({
      id: 'abc',
      status: RunStatus.CANCELED,
      startTime: START_TIME,
      endTime: END_TIME,
    });

    render(
      <TimeProvider>
        <RunTimingDetails loading={false} run={run} />
      </TimeProvider>,
    );

    await screen.findByRole('table');
    expect(screen.getByRole('row', {name: /started feb 17, 6:24:30 am/i})).toBeVisible();
    expect(screen.getByRole('row', {name: /ended feb 17, 6:25:16 am/i})).toBeVisible();
    expect(screen.getByRole('row', {name: /duration timer 0:00:46/i})).toBeVisible();
  });

  it('renders CANCELED details without start time', async () => {
    const run = buildRun({
      id: 'abc',
      status: RunStatus.CANCELED,
      startTime: null,
      endTime: END_TIME,
    });

    render(
      <TimeProvider>
        <RunTimingDetails loading={false} run={run} />
      </TimeProvider>,
    );

    await screen.findByRole('table');
    expect(screen.getByRole('row', {name: /started canceled/i})).toBeVisible();
    expect(screen.getByRole('row', {name: /ended feb 17, 6:25:16 am/i})).toBeVisible();
    expect(screen.getByRole('row', {name: /duration canceled/i})).toBeVisible();
  });

  it('renders CANCELING details', async () => {
    const run = buildRun({
      id: 'abc',
      status: RunStatus.CANCELING,
      startTime: START_TIME,
      endTime: null,
    });

    render(
      <TimeProvider>
        <RunTimingDetails loading={false} run={run} />
      </TimeProvider>,
    );

    await screen.findByRole('table');
    expect(screen.getByRole('row', {name: /started feb 17, 6:24:30 am/i})).toBeVisible();
    expect(screen.getByRole('row', {name: /ended canceling/i})).toBeVisible();
    expect(screen.getByRole('row', {name: /duration timer 0:01:01/i})).toBeVisible();
  });

  it('renders FAILURE details with start time', async () => {
    const run = buildRun({
      id: 'abc',
      status: RunStatus.FAILURE,
      startTime: START_TIME,
      endTime: END_TIME,
    });

    render(
      <TimeProvider>
        <RunTimingDetails loading={false} run={run} />
      </TimeProvider>,
    );

    await screen.findByRole('table');
    expect(screen.getByRole('row', {name: /started feb 17, 6:24:30 am/i})).toBeVisible();
    expect(screen.getByRole('row', {name: /ended feb 17, 6:25:16 am/i})).toBeVisible();
    expect(screen.getByRole('row', {name: /duration timer 0:00:46/i})).toBeVisible();
  });

  it('renders FAILURE details without start time', async () => {
    const run = buildRun({
      id: 'abc',
      status: RunStatus.FAILURE,
      startTime: null,
      endTime: END_TIME,
    });

    render(
      <TimeProvider>
        <RunTimingDetails loading={false} run={run} />
      </TimeProvider>,
    );

    await screen.findByRole('table');
    expect(screen.getByRole('row', {name: /started failed/i})).toBeVisible();
    expect(screen.getByRole('row', {name: /ended feb 17, 6:25:16 am/i})).toBeVisible();
    expect(screen.getByRole('row', {name: /duration failed/i})).toBeVisible();
  });

  it('renders NOT_STARTED details', async () => {
    const run = buildRun({
      id: 'abc',
      status: RunStatus.NOT_STARTED,
      startTime: null,
      endTime: null,
    });

    render(
      <TimeProvider>
        <RunTimingDetails loading={false} run={run} />
      </TimeProvider>,
    );

    await screen.findByRole('table');
    expect(screen.getByRole('row', {name: /started waiting to start…/i})).toBeVisible();
    expect(screen.getByRole('row', {name: /ended waiting to start…/i})).toBeVisible();
    expect(screen.getByRole('row', {name: /duration waiting to start…/i})).toBeVisible();
  });

  it('renders STARTED details', async () => {
    const run = buildRun({
      id: 'abc',
      status: RunStatus.STARTED,
      startTime: START_TIME,
      endTime: null,
    });

    render(
      <TimeProvider>
        <RunTimingDetails loading={false} run={run} />
      </TimeProvider>,
    );

    await screen.findByRole('table');
    expect(screen.getByRole('row', {name: /started feb 17, 6:24:30 am/i})).toBeVisible();
    expect(screen.getByRole('row', {name: /ended started…/i})).toBeVisible();
    expect(screen.getByRole('row', {name: /duration timer 0:01:01/i})).toBeVisible();
  });

  it('renders STARTING details with start time', async () => {
    const run = buildRun({
      id: 'abc',
      status: RunStatus.STARTING,
      startTime: START_TIME,
      endTime: null,
    });

    render(
      <TimeProvider>
        <RunTimingDetails loading={false} run={run} />
      </TimeProvider>,
    );

    await screen.findByRole('table');
    expect(screen.getByRole('row', {name: /started feb 17, 6:24:30 am/i})).toBeVisible();
    expect(screen.getByRole('row', {name: /ended starting…/i})).toBeVisible();
    expect(screen.getByRole('row', {name: /duration timer 0:01:01/i})).toBeVisible();
  });

  it('renders STARTING details without start time', async () => {
    const run = buildRun({
      id: 'abc',
      status: RunStatus.STARTING,
      startTime: null,
      endTime: null,
    });

    render(
      <TimeProvider>
        <RunTimingDetails loading={false} run={run} />
      </TimeProvider>,
    );

    await screen.findByRole('table');
    expect(screen.getByRole('row', {name: /started starting…/i})).toBeVisible();
    expect(screen.getByRole('row', {name: /ended starting…/i})).toBeVisible();
    expect(screen.getByRole('row', {name: /duration starting…/i})).toBeVisible();
  });

  it('renders SUCCESS details', async () => {
    const run = buildRun({
      id: 'abc',
      status: RunStatus.SUCCESS,
      startTime: START_TIME,
      endTime: END_TIME,
    });

    render(
      <TimeProvider>
        <RunTimingDetails loading={false} run={run} />
      </TimeProvider>,
    );

    await screen.findByRole('table');
    expect(screen.getByRole('row', {name: /started feb 17, 6:24:30 am/i})).toBeVisible();
    expect(screen.getByRole('row', {name: /ended feb 17, 6:25:16 am/i})).toBeVisible();
    expect(screen.getByRole('row', {name: /duration timer 0:00:46/i})).toBeVisible();
  });
});
