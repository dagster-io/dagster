import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {render, screen} from '@testing-library/react';
import {MemoryRouter} from 'react-router';

import {RunStatus, buildPipeline, buildRun, buildRuns, buildSchedule} from '../../graphql/types';
import {DagsterTag} from '../../runs/RunTag';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {repoAddressAsTag} from '../../workspace/repoAddressAsString';
import {JOB_METADATA_QUERY, JobMetadata} from '../JobMetadata';
import {LATEST_RUN_TAG_QUERY} from '../LatestRunTag';
import {JobMetadataQuery, JobMetadataQueryVariables} from '../types/JobMetadata.types';
import {LatestRunTagQuery, LatestRunTagQueryVariables} from '../types/LatestRunTag.types';

jest.mock('../../app/Flags');

jest.mock('../ScheduleOrSensorTag', () => ({
  ScheduleOrSensorTag: () => <div>Schedule/sensor tag</div>,
}));

// Jan 1, 2020
const START_TIME = 1577858400;

describe('JobMetadata', () => {
  const PIPELINE_NAME = 'my_pipeline';
  const REPO_ADDRESS = buildRepoAddress('foo', 'bar');

  const buildJobMetadataQuery = (): MockedResponse<JobMetadataQuery, JobMetadataQueryVariables> => {
    return {
      request: {
        query: JOB_METADATA_QUERY,
        variables: {
          runsFilter: {
            pipelineName: PIPELINE_NAME,
            tags: [
              {
                key: DagsterTag.RepositoryLabelTag,
                value: repoAddressAsTag(REPO_ADDRESS),
              },
            ],
          },
          params: {
            pipelineName: PIPELINE_NAME,
            repositoryName: REPO_ADDRESS.name,
            repositoryLocationName: REPO_ADDRESS.location,
          },
        },
      },
      result: {
        data: {
          __typename: 'Query',
          assetNodes: [],
          pipelineOrError: buildPipeline({
            name: PIPELINE_NAME,
            schedules: [buildSchedule()],
          }),
          pipelineRunsOrError: buildRuns({
            results: [
              buildRun({
                status: RunStatus.SUCCESS,
                pipelineName: PIPELINE_NAME,
                startTime: START_TIME,
                updateTime: START_TIME,
                endTime: START_TIME + 1,
              }),
            ],
          }),
        },
      },
    };
  };

  const buildLatestRunTagQuery = (): MockedResponse<
    LatestRunTagQuery,
    LatestRunTagQueryVariables
  > => {
    return {
      request: {
        query: LATEST_RUN_TAG_QUERY,
        variables: {
          runsFilter: {
            pipelineName: PIPELINE_NAME,
            tags: [
              {
                key: DagsterTag.RepositoryLabelTag,
                value: repoAddressAsTag(REPO_ADDRESS),
              },
            ],
          },
        },
      },
      result: {
        data: {
          __typename: 'Query',
          pipelineRunsOrError: buildRuns({
            results: [
              buildRun({
                id: '0123',
                status: RunStatus.SUCCESS,
                pipelineName: PIPELINE_NAME,
                startTime: START_TIME,
                updateTime: START_TIME,
                endTime: START_TIME + 1,
              }),
            ],
          }),
        },
      },
    };
  };

  it('renders latest run info and schedule/sensor', async () => {
    render(
      <MemoryRouter>
        <MockedProvider mocks={[buildJobMetadataQuery(), buildLatestRunTagQuery()]}>
          <JobMetadata pipelineName={PIPELINE_NAME} repoAddress={REPO_ADDRESS} />
        </MockedProvider>
      </MemoryRouter>,
    );

    expect(await screen.findByText(/latest run:/i)).toBeVisible();
    expect(await screen.findByRole('link', {name: /jan 1/i})).toBeVisible();

    // Render mocked schedule/sensor tag
    expect(await screen.findByText(/schedule\/sensor tag/i)).toBeVisible();
  });
});
