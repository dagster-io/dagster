import faker from 'faker';

import {
  buildDagsterLibraryVersion,
  buildPipeline,
  buildRepository,
  buildRepositoryLocation,
  buildRepositoryMetadata,
  buildResourceDetails,
  buildSchedule,
  buildSensor,
  buildWorkspaceLocationEntry,
} from '../../graphql/types';

export const buildEmptyWorkspaceLocationEntry = (config: {time: number; locationName: string}) => {
  const {time, locationName} = config;
  return buildWorkspaceLocationEntry({
    updatedTimestamp: time,
    name: locationName,
    displayMetadata: [
      buildRepositoryMetadata({
        key: 'image',
        value:
          'whereami.kz.almaty-2.amazonaws.com/whoami:whoami-b0d8eb5c3518ddd5640657075-cb6978e44008',
      }),
      buildRepositoryMetadata({key: 'module_name', value: 'my.cool.module'}),
      buildRepositoryMetadata({key: 'working_directory', value: '/foo/bar/baz'}),
      buildRepositoryMetadata({
        key: 'commit_hash',
        value: '3c88b0248f9b66f2a49e154e4731fe70',
      }),
      buildRepositoryMetadata({
        key: 'url',
        value: 'https://github.com/supercool-org/foobar/tree/3c88b0248f9b66f2a49e154e4731fe70',
      }),
    ],
    locationOrLoadError: buildRepositoryLocation({
      name: locationName,
      dagsterLibraryVersions: [
        buildDagsterLibraryVersion({
          name: 'dagster',
          version: '1.8',
        }),
      ],
    }),
  });
};

export const buildSampleRepository = (config: {
  name: string;
  jobCount: number;
  scheduleCount: number;
  sensorCount: number;
  resourceCount: number;
}) => {
  const {name, jobCount, scheduleCount, sensorCount, resourceCount} = config;
  return buildRepository({
    id: name,
    name,
    pipelines: new Array(jobCount).fill(null).map(() => {
      return buildPipeline({
        name: faker.random.words(2).split(' ').join('-').toLowerCase(),
        isJob: true,
      });
    }),
    schedules: new Array(scheduleCount).fill(null).map(() => {
      return buildSchedule({
        name: faker.random.words(2).split(' ').join('-').toLowerCase(),
      });
    }),
    sensors: new Array(sensorCount).fill(null).map(() => {
      return buildSensor({
        name: faker.random.words(10).split(' ').join('-').toLowerCase(),
      });
    }),
    allTopLevelResourceDetails: new Array(resourceCount).fill(null).map(() => {
      return buildResourceDetails({
        name: faker.random.words(2).split(' ').join('-').toLowerCase(),
      });
    }),
  });
};
