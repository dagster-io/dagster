import * as React from 'react';
import {render, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter} from 'react-router';

import {
  InstigationStatus,
  buildInstigationState,
  buildSchedule,
  buildSensor,
} from '../../graphql/types';
import {DUNDER_REPO_NAME, buildRepoAddress} from '../../workspace/buildRepoAddress';
import {ScheduleOrSensorTag} from '../ScheduleOrSensorTag';

describe('ScheduleOrSensorTag', () => {
  const CODE_LOCATION = 'my-location';
  const SCHEDULE_NAME_A = 'my-schedule-a';
  const SCHEDULE_NAME_B = 'my-schedule-b';
  const SENSOR_NAME_A = 'my-sensor-a';
  const SENSOR_NAME_B = 'my-sensor-b';

  const REPO_ADDRESS = buildRepoAddress(DUNDER_REPO_NAME, CODE_LOCATION);

  const SCHEDULE_A = buildSchedule({
    name: SCHEDULE_NAME_A,
    cronSchedule: '* * * * *',
    executionTimezone: 'America/Chicago',
    scheduleState: buildInstigationState({
      status: InstigationStatus.RUNNING,
    }),
  });

  const SCHEDULE_B = buildSchedule({
    name: SCHEDULE_NAME_B,
    cronSchedule: '1 * * * *',
    executionTimezone: 'America/Chicago',
    scheduleState: buildInstigationState({
      status: InstigationStatus.RUNNING,
    }),
  });

  const SENSOR_A = buildSensor({
    name: SENSOR_NAME_A,
    sensorState: buildInstigationState({
      status: InstigationStatus.RUNNING,
    }),
  });

  const SENSOR_B = buildSensor({
    name: SENSOR_NAME_B,
    sensorState: buildInstigationState({
      status: InstigationStatus.RUNNING,
    }),
  });

  it('renders empty message if no schedules or sensors', async () => {
    render(<ScheduleOrSensorTag repoAddress={REPO_ADDRESS} />);
    expect(await screen.findByText(/no schedules or sensors/i)).toBeInTheDocument();
  });

  it('renders single schedule', async () => {
    render(
      <MemoryRouter>
        <ScheduleOrSensorTag
          repoAddress={REPO_ADDRESS}
          schedules={[SCHEDULE_A]}
          showSwitch={false}
        />
      </MemoryRouter>,
    );
    const link = await screen.findByRole('link', {name: /every minute/i});
    expect(link).toBeVisible();
    expect(link.getAttribute('href')).toBe(
      `/locations/${CODE_LOCATION}/schedules/${SCHEDULE_NAME_A}`,
    );
  });

  it('renders multiple schedules', async () => {
    const event = userEvent.setup();

    render(
      <MemoryRouter>
        <ScheduleOrSensorTag
          repoAddress={REPO_ADDRESS}
          schedules={[SCHEDULE_A, SCHEDULE_B]}
          showSwitch={false}
        />
      </MemoryRouter>,
    );

    const buttonLink = await screen.findByRole('button', {name: /2 schedules/i});
    expect(buttonLink).toBeVisible();

    await event.click(buttonLink);

    const linkA = await screen.findByRole('link', {name: /my-schedule-a/i});
    expect(linkA.getAttribute('href')).toBe(
      `/locations/${CODE_LOCATION}/schedules/${SCHEDULE_NAME_A}`,
    );

    const linkB = await screen.findByRole('link', {name: /my-schedule-b/i});
    expect(linkB.getAttribute('href')).toBe(
      `/locations/${CODE_LOCATION}/schedules/${SCHEDULE_NAME_B}`,
    );
  });

  it('renders single sensor', async () => {
    render(
      <MemoryRouter>
        <ScheduleOrSensorTag repoAddress={REPO_ADDRESS} sensors={[SENSOR_A]} showSwitch={false} />
      </MemoryRouter>,
    );
    const link = await screen.findByRole('link', {name: /my-sensor-a/i});
    expect(link).toBeVisible();
    expect(link.getAttribute('href')).toBe(`/locations/${CODE_LOCATION}/sensors/${SENSOR_NAME_A}`);
  });

  it('renders multiple sensors', async () => {
    const event = userEvent.setup();

    render(
      <MemoryRouter>
        <ScheduleOrSensorTag
          repoAddress={REPO_ADDRESS}
          sensors={[SENSOR_A, SENSOR_B]}
          showSwitch={false}
        />
      </MemoryRouter>,
    );

    const buttonLink = await screen.findByRole('button', {name: /2 sensors/i});
    expect(buttonLink).toBeVisible();

    await event.click(buttonLink);

    const linkA = await screen.findByRole('link', {name: /my-sensor-a/i});
    expect(linkA.getAttribute('href')).toBe(`/locations/${CODE_LOCATION}/sensors/${SENSOR_NAME_A}`);

    const linkB = await screen.findByRole('link', {name: /my-sensor-b/i});
    expect(linkB.getAttribute('href')).toBe(`/locations/${CODE_LOCATION}/sensors/${SENSOR_NAME_B}`);
  });

  it('renders multiple schedules AND sensors', async () => {
    const event = userEvent.setup();

    render(
      <MemoryRouter>
        <ScheduleOrSensorTag
          repoAddress={REPO_ADDRESS}
          schedules={[SCHEDULE_A, SCHEDULE_B]}
          sensors={[SENSOR_A, SENSOR_B]}
          showSwitch={false}
        />
      </MemoryRouter>,
    );

    const buttonLink = await screen.findByRole('button', {name: /4 schedules\/sensors/i});
    expect(buttonLink).toBeVisible();

    await event.click(buttonLink);

    const scheduleLinkA = await screen.findByRole('link', {name: /my-schedule-a/i});
    expect(scheduleLinkA.getAttribute('href')).toBe(
      `/locations/${CODE_LOCATION}/schedules/${SCHEDULE_NAME_A}`,
    );

    const scheduleLinkB = await screen.findByRole('link', {name: /my-schedule-b/i});
    expect(scheduleLinkB.getAttribute('href')).toBe(
      `/locations/${CODE_LOCATION}/schedules/${SCHEDULE_NAME_B}`,
    );

    const sensorLinkA = await screen.findByRole('link', {name: /my-sensor-a/i});
    expect(sensorLinkA.getAttribute('href')).toBe(
      `/locations/${CODE_LOCATION}/sensors/${SENSOR_NAME_A}`,
    );

    const sensorLinkB = await screen.findByRole('link', {name: /my-sensor-b/i});
    expect(sensorLinkB.getAttribute('href')).toBe(
      `/locations/${CODE_LOCATION}/sensors/${SENSOR_NAME_B}`,
    );
  });
});
