import faker from 'faker';

import {RunStatus} from '../graphql/types';

export const generateRunMocks = (runCount: number, range: [number, number]) => {
  const [start, end] = range;
  const now = Date.now();
  return [...new Array(runCount)]
    .map(() => faker.date.between(new Date(start), new Date(end)))
    .map((startDate) => {
      const endTime = Math.min(startDate.getTime() + faker.datatype.number() * 10, now);
      const status =
        endTime === now
          ? RunStatus.STARTED
          : faker.random.arrayElement([RunStatus.SUCCESS, RunStatus.FAILURE]);

      const startTime = startDate.getTime();
      return {
        id: faker.datatype.uuid(),
        creationTime: startTime,
        startTime,
        status,
        endTime,
        automation: null,
        externalJobSource: null,
      };
    });
};
