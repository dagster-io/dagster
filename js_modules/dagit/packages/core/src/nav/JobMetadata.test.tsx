import {render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';

import * as Flags from '../app/Flags';
import {TestProvider} from '../testing/TestProvider';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

import {JobMetadata} from './JobMetadata';

jest.mock('../app/Flags');

// Jan 1, 2020
const START_TIME = 1577858400;

describe('JobMetadata', () => {
  const PIPELINE_NAME = 'my_pipeline';
  const PIPELINE_MODE = 'my_mode';
  const REPO_ADDRESS = buildRepoAddress('foo', 'bar');

  const defaultMocks = {
    Pipeline: () => ({
      name: () => 'my_pipeline',
      schedules: () => [],
      sensors: () => [],
    }),
    Run: () => ({
      id: () => 'abc',
      startTime: () => START_TIME,
      updateTime: () => START_TIME,
      endTime: () => START_TIME + 1,
    }),
    PipelineRun: () => ({
      id: () => 'abc',
      startTime: () => START_TIME,
      updateTime: () => START_TIME,
      endTime: () => START_TIME + 1,
    }),
    PipelineRunStatsSnapshot: () => ({
      startTime: () => START_TIME,
      launchTime: () => START_TIME,
      endTime: () => START_TIME + 1,
    }),
    RunStatsSnapshot: () => ({
      startTime: () => START_TIME,
      launchTime: () => START_TIME,
      endTime: () => START_TIME + 1,
    }),
    Mode: () => ({
      name: () => 'my_mode',
    }),
    Repository: () => ({
      name: () => 'foo',
    }),
    RepositoryLocation: () => ({
      name: () => 'bar',
    }),
    Schedule: () => ({
      name: () => 'cool_schedule',
      mode: () => 'my_mode',
      cronSchedule: () => '(*/5 * * * *)',
    }),
    Sensor: () => ({
      name: () => 'cool_sensor',
      targets: () => [...new Array(1)],
    }),
    Target: () => ({
      pipelineName: () => PIPELINE_NAME,
      mode: () => PIPELINE_MODE,
    }),
  };

  const JobMetadataContainer = () => {
    return <JobMetadata pipelineName={PIPELINE_NAME} repoAddress={REPO_ADDRESS} />;
  };

  const renderWithMocks = (mocks?: any) => {
    render(
      <TestProvider apolloProps={{mocks: mocks ? [defaultMocks, mocks] : defaultMocks}}>
        <JobMetadataContainer />
      </TestProvider>,
    );
  };

  describe('Schedules/sensors', () => {
    describe('Crag flag OFF', () => {
      const useFeatureFlags = Flags.useFeatureFlags;
      beforeAll(() => {
        Object.defineProperty(Flags, 'useFeatureFlags', {
          value: jest.fn().mockImplementation(() => ({flagPipelineModeTuples: false})),
        });
      });

      afterAll(() => {
        Object.defineProperty(Flags, 'useFeatureFlags', useFeatureFlags);
      });

      it('renders empty state', async () => {
        renderWithMocks();
        await waitFor(() => {
          expect(screen.getByText(/latest run:/i)).toBeVisible();
          expect(screen.getByRole('link', {name: /jan 1/i})).toBeVisible();
        });
      });

      it('renders single schedule', async () => {
        const mocks = {
          Pipeline: () => ({
            name: () => PIPELINE_NAME,
            schedules: () => [...new Array(1)],
            sensors: () => [],
          }),
        };

        renderWithMocks(mocks);

        await waitFor(() => {
          expect(screen.getByText(/schedule:/i)).toBeVisible();
          expect(screen.getByRole('link', {name: /every 5 minutes/i})).toBeVisible();
        });
      });

      it('renders multiple schedules', async () => {
        const mocks = {
          Pipeline: () => ({
            name: () => PIPELINE_NAME,
            schedules: () => [...new Array(2)],
            sensors: () => [],
          }),
        };

        renderWithMocks(mocks);
        await waitFor(() => {
          expect(screen.getByRole('button', {name: /view 2 schedules/i})).toBeVisible();
        });
      });

      it('renders single sensor', async () => {
        const mocks = {
          Pipeline: () => ({
            name: () => PIPELINE_NAME,
            schedules: () => [],
            sensors: () => [...new Array(1)],
          }),
        };

        renderWithMocks(mocks);
        await waitFor(() => {
          expect(screen.getByText(/sensor:/i)).toBeVisible();
          expect(screen.getByRole('link', {name: /cool_sensor/i})).toBeVisible();
        });
      });

      it('renders multiple sensors', async () => {
        const mocks = {
          Pipeline: () => ({
            name: () => PIPELINE_NAME,
            schedules: () => [],
            sensors: () => [...new Array(2)],
          }),
        };

        renderWithMocks(mocks);
        await waitFor(() => {
          expect(screen.getByRole('button', {name: /view 2 sensors/i})).toBeVisible();
        });
      });

      it('renders multiple of each', async () => {
        const mocks = {
          Pipeline: () => ({
            name: () => PIPELINE_NAME,
            schedules: () => [...new Array(2)],
            sensors: () => [...new Array(2)],
          }),
        };

        renderWithMocks(mocks);
        await waitFor(() => {
          expect(screen.getByRole('button', {name: /view 4 schedules\/sensors/i})).toBeVisible();
        });
      });
    });

    describe('Crag flag ON', () => {
      const useFeatureFlags = Flags.useFeatureFlags;
      beforeAll(() => {
        Object.defineProperty(Flags, 'useFeatureFlags', {
          value: jest.fn().mockImplementation(() => ({flagPipelineModeTuples: true})),
        });
      });

      afterAll(() => {
        Object.defineProperty(Flags, 'useFeatureFlags', useFeatureFlags);
      });

      it('renders empty state', async () => {
        renderWithMocks();
        await waitFor(() => {
          expect(screen.getByText(/latest run:/i)).toBeVisible();
          expect(screen.getByRole('link', {name: /jan 1/i})).toBeVisible();
        });
      });

      it('renders empty if no matching mode', async () => {
        const mocks = {
          Pipeline: () => ({
            name: () => PIPELINE_NAME,
            schedules: () => [...new Array(1)],
            sensors: () => [...new Array(1)],
          }),
          Schedule: () => ({
            mode: () => 'mismatching_mode',
          }),
          Sensor: () => ({
            targets: () => [
              {
                pipelineName: PIPELINE_NAME,
                mode: 'mistmatching_mode',
              },
            ],
          }),
        };

        renderWithMocks(mocks);
        await waitFor(() => {
          expect(screen.queryByText(/schedule:/i)).toBeNull();
          expect(screen.queryByRole('link', {name: /every 5 minutes/i})).toBeNull();
        });
      });

      it('renders single schedule with matching mode', async () => {
        const mocks = {
          Pipeline: () => ({
            name: () => PIPELINE_NAME,
            schedules: () => [...new Array(1)],
            sensors: () => [],
          }),
        };

        renderWithMocks(mocks);
        await waitFor(() => {
          expect(screen.getByText(/schedule:/i)).toBeVisible();
          expect(screen.getByRole('link', {name: /every 5 minutes/i})).toBeVisible();
        });
      });

      it('renders multiple schedules if matching mode', async () => {
        const mocks = {
          Pipeline: () => ({
            name: () => PIPELINE_NAME,
            schedules: () => [...new Array(2)],
            sensors: () => [],
          }),
        };

        renderWithMocks(mocks);
        await waitFor(() => {
          expect(screen.getByRole('button', {name: /view 2 schedules/i})).toBeVisible();
        });
      });

      it('renders single sensor if matching mode', async () => {
        const mocks = {
          Pipeline: () => ({
            name: () => PIPELINE_NAME,
            schedules: () => [],
            sensors: () => [...new Array(1)],
          }),
        };

        renderWithMocks(mocks);
        await waitFor(() => {
          expect(screen.getByText(/sensor:/i)).toBeVisible();
          expect(screen.getByRole('link', {name: /cool_sensor/i})).toBeVisible();
        });
      });

      it('renders multiple sensors if matching mode', async () => {
        const mocks = {
          Pipeline: () => ({
            name: () => PIPELINE_NAME,
            schedules: () => [],
            sensors: () => [...new Array(2)],
          }),
        };

        renderWithMocks(mocks);
        await waitFor(() => {
          expect(screen.getByRole('button', {name: /view 2 sensors/i})).toBeVisible();
        });
      });

      it('renders multiple of each if matching mode', async () => {
        const mocks = {
          Pipeline: () => ({
            name: () => PIPELINE_NAME,
            schedules: () => [...new Array(2)],
            sensors: () => [...new Array(2)],
          }),
        };

        renderWithMocks(mocks);
        await waitFor(() => {
          expect(screen.getByRole('button', {name: /view 4 schedules\/sensors/i})).toBeVisible();
        });
      });
    });
  });
});
