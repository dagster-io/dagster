import {MockList} from '@graphql-tools/mock';
import {render, screen, waitFor, within} from '@testing-library/react';
import * as React from 'react';

import * as Flags from '../app/Flags';
import {TestProvider} from '../testing/TestProvider';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

import {JobMetadata} from './JobMetadata';

jest.mock('../app/Flags');

describe('JobMetadata', () => {
  const PIPELINE_NAME = 'my_pipeline';
  const PIPELINE_MODE = 'my_mode';
  const REPO_ADDRESS = buildRepoAddress('foo', 'bar');

  const defaultMocks = {
    Pipeline: () => ({
      name: () => 'my_pipeline',
      schedules: () => new MockList(0),
      sensors: () => new MockList(0),
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
    }),
    Sensor: () => ({
      name: () => 'cool_sensor',
      targets: () => new MockList(1),
    }),
    Target: () => ({
      pipelineName: () => PIPELINE_NAME,
      mode: () => PIPELINE_MODE,
    }),
  };

  const renderWithMocks = (mocks?: any) => {
    render(
      <TestProvider apolloProps={{mocks: mocks ? [defaultMocks, mocks] : defaultMocks}}>
        <JobMetadata
          pipelineName={PIPELINE_NAME}
          pipelineMode={PIPELINE_MODE}
          repoAddress={REPO_ADDRESS}
        />
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
          const row = screen.getByRole('row', {name: /schedule\/sensor/i});
          expect(within(row).getByText(/none/i)).toBeVisible();
        });
      });

      it('renders single schedule', async () => {
        const mocks = {
          Pipeline: () => ({
            name: () => PIPELINE_NAME,
            schedules: () => new MockList(1),
            sensors: () => new MockList(0),
          }),
          Schedule: () => ({
            name: () => 'cool_schedule',
          }),
        };

        renderWithMocks(mocks);

        await waitFor(() => {
          const row = screen.getByRole('row', {name: /schedule\/sensor/i});
          const link = within(row).getByRole('link');
          expect(link).toBeVisible();
          expect(link.textContent).toMatch(/cool_schedule/i);
        });
      });

      it('renders multiple schedules', async () => {
        const mocks = {
          Pipeline: () => ({
            name: () => PIPELINE_NAME,
            schedules: () => new MockList(2),
            sensors: () => new MockList(0),
          }),
        };

        renderWithMocks(mocks);
        await waitFor(() => {
          const row = screen.getByRole('row', {name: /schedule\/sensor/i});
          const link = within(row).getByRole('button');
          expect(link).toBeVisible();
          expect(link.textContent).toMatch(/view 2 schedules/i);
        });
      });

      it('renders single sensor', async () => {
        const mocks = {
          Pipeline: () => ({
            name: () => PIPELINE_NAME,
            schedules: () => new MockList(0),
            sensors: () => new MockList(1),
          }),
        };

        renderWithMocks(mocks);
        await waitFor(() => {
          const row = screen.getByRole('row', {name: /schedule\/sensor/i});
          const link = within(row).getByRole('link');
          expect(link).toBeVisible();
          expect(link.textContent).toMatch(/cool_sensor/i);
        });
      });

      it('renders multiple sensors', async () => {
        const mocks = {
          Pipeline: () => ({
            name: () => PIPELINE_NAME,
            schedules: () => new MockList(0),
            sensors: () => new MockList(2),
          }),
        };

        renderWithMocks(mocks);
        await waitFor(() => {
          const row = screen.getByRole('row', {name: /schedule\/sensor/i});
          const link = within(row).getByRole('button');
          expect(link).toBeVisible();
          expect(link.textContent).toMatch(/view 2 sensors/i);
        });
      });

      it('renders multiple of each', async () => {
        const mocks = {
          Pipeline: () => ({
            name: () => PIPELINE_NAME,
            schedules: () => new MockList(2),
            sensors: () => new MockList(2),
          }),
        };

        renderWithMocks(mocks);
        await waitFor(() => {
          const row = screen.getByRole('row', {name: /schedule\/sensor/i});
          const link = within(row).getByRole('button');
          expect(link).toBeVisible();
          expect(link.textContent).toMatch(/view 4 schedules\/sensors/i);
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
          const row = screen.getByRole('row', {name: /schedule\/sensor/i});
          expect(within(row).getByText(/none/i)).toBeVisible();
        });
      });

      it('renders empty if no matching mode', async () => {
        const mocks = {
          Pipeline: () => ({
            name: () => PIPELINE_NAME,
            schedules: () => new MockList(1),
            sensors: () => new MockList(1),
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
          const row = screen.getByRole('row', {name: /schedule\/sensor/i});
          expect(within(row).getByText(/none/i)).toBeVisible();
        });
      });

      it('renders single schedule with matching mode', async () => {
        const mocks = {
          Pipeline: () => ({
            name: () => PIPELINE_NAME,
            schedules: () => new MockList(1),
            sensors: () => new MockList(0),
          }),
        };

        renderWithMocks(mocks);

        await waitFor(() => {
          const row = screen.getByRole('row', {name: /schedule\/sensor/i});
          const link = within(row).getByRole('link');
          expect(link).toBeVisible();
          expect(link.textContent).toMatch(/cool_schedule/i);
        });
      });

      it('renders multiple schedules if matching mode', async () => {
        const mocks = {
          Pipeline: () => ({
            name: () => PIPELINE_NAME,
            schedules: () => new MockList(2),
            sensors: () => new MockList(0),
          }),
        };

        renderWithMocks(mocks);
        await waitFor(() => {
          const row = screen.getByRole('row', {name: /schedule\/sensor/i});
          const link = within(row).getByRole('button');
          expect(link).toBeVisible();
          expect(link.textContent).toMatch(/view 2 schedules/i);
        });
      });

      it('renders single sensor if matching mode', async () => {
        const mocks = {
          Pipeline: () => ({
            name: () => PIPELINE_NAME,
            schedules: () => new MockList(0),
            sensors: () => new MockList(1),
          }),
        };

        renderWithMocks(mocks);
        await waitFor(() => {
          const row = screen.getByRole('row', {name: /schedule\/sensor/i});
          const link = within(row).getByRole('link');
          expect(link).toBeVisible();
          expect(link.textContent).toMatch(/cool_sensor/i);
        });
      });

      it('renders multiple sensors if matching mode', async () => {
        const mocks = {
          Pipeline: () => ({
            name: () => PIPELINE_NAME,
            schedules: () => new MockList(0),
            sensors: () => new MockList(2),
          }),
        };

        renderWithMocks(mocks);
        await waitFor(() => {
          const row = screen.getByRole('row', {name: /schedule\/sensor/i});
          const link = within(row).getByRole('button');
          expect(link).toBeVisible();
          expect(link.textContent).toMatch(/view 2 sensors/i);
        });
      });

      it('renders multiple of each if matching mode', async () => {
        const mocks = {
          Pipeline: () => ({
            name: () => PIPELINE_NAME,
            schedules: () => new MockList(2),
            sensors: () => new MockList(2),
          }),
        };

        renderWithMocks(mocks);
        await waitFor(() => {
          const row = screen.getByRole('row', {name: /schedule\/sensor/i});
          const link = within(row).getByRole('button');
          expect(link).toBeVisible();
          expect(link.textContent).toMatch(/view 4 schedules\/sensors/i);
        });
      });
    });
  });
});
