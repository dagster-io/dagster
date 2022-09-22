import {Colors} from '@dagster-io/ui';

import {RunStatus} from '../types/globalTypes';

import {TimelineRun} from './RunTimeline';
import {mergeStatusToBackground} from './mergeStatusToBackground';

describe('mergeStatusToBackground', () => {
  const failedA = {id: 'failed-a', status: RunStatus.FAILURE, startTime: 10, endTime: 50};
  const failedB = {id: 'failed-b', status: RunStatus.FAILURE, startTime: 10, endTime: 50};
  const succeededA = {id: 'succeeded-a', status: RunStatus.SUCCESS, startTime: 10, endTime: 50};
  const succeededB = {id: 'succeeded-b', status: RunStatus.SUCCESS, startTime: 10, endTime: 50};
  const inProgressA = {id: 'inProgress-a', status: RunStatus.STARTED, startTime: 10, endTime: 50};
  const inProgressB = {id: 'inProgress-b', status: RunStatus.STARTED, startTime: 10, endTime: 50};
  const queuedA = {id: 'queued-a', status: RunStatus.QUEUED, startTime: 10, endTime: 50};
  const queuedB = {id: 'queued-b', status: RunStatus.QUEUED, startTime: 10, endTime: 50};
  const scheduledA: TimelineRun = {
    id: 'scheduled-a',
    status: 'SCHEDULED',
    startTime: 10,
    endTime: 50,
  };
  const scheduledB: TimelineRun = {
    id: 'scheduled-b',
    status: 'SCHEDULED',
    startTime: 10,
    endTime: 50,
  };

  it('uses a single color if all runs are the same status', () => {
    expect(mergeStatusToBackground([failedA, failedB])).toBe(Colors.Red500);
    expect(mergeStatusToBackground([succeededA, succeededB])).toBe(Colors.Green500);
    expect(mergeStatusToBackground([inProgressA, inProgressB])).toBe(Colors.Blue500);
    expect(mergeStatusToBackground([queuedA, queuedB])).toBe(Colors.Blue200);
    expect(mergeStatusToBackground([scheduledA, scheduledB])).toBe(Colors.Blue200);
  });

  it('splits the background if there are two statuses, in order', () => {
    const failedSucceeded = mergeStatusToBackground([failedA, succeededA]);
    expect(failedSucceeded).toBe(
      `linear-gradient(to right, ${Colors.Red500} 50.0%, ${Colors.Green500} 50.0%)`,
    );
    const succeededFailed = mergeStatusToBackground([succeededA, failedA]);
    expect(succeededFailed).toBe(
      `linear-gradient(to right, ${Colors.Red500} 50.0%, ${Colors.Green500} 50.0%)`,
    );
    const succeededInProgress = mergeStatusToBackground([succeededA, inProgressA]);
    expect(succeededInProgress).toBe(
      `linear-gradient(to right, ${Colors.Green500} 50.0%, ${Colors.Blue500} 50.0%)`,
    );

    // More than two runs
    const failFailSuccess = mergeStatusToBackground([failedA, failedB, succeededA]);
    expect(failFailSuccess).toBe(
      `linear-gradient(to right, ${Colors.Red500} 66.7%, ${Colors.Green500} 66.7%)`,
    );
  });

  it('splits the background if there are 3+ statuses, in order', () => {
    const succeedFailInProgress = mergeStatusToBackground([succeededA, failedA, inProgressA]);
    expect(succeedFailInProgress).toBe(
      `linear-gradient(to right, ${Colors.Red500} 33.3%, ${Colors.Green500} 33.3% 66.7%, ${Colors.Blue500} 66.7%)`,
    );

    const succeed2xFailInProgress = mergeStatusToBackground([
      succeededA,
      succeededB,
      failedA,
      inProgressA,
    ]);
    expect(succeed2xFailInProgress).toBe(
      `linear-gradient(to right, ${Colors.Red500} 25.0%, ${Colors.Green500} 25.0% 75.0%, ${Colors.Blue500} 75.0%)`,
    );

    const allOfTheAbove = mergeStatusToBackground([
      succeededA,
      failedA,
      inProgressA,
      queuedA,
      scheduledA,
    ]);
    expect(allOfTheAbove).toBe(
      `linear-gradient(to right, ${Colors.Red500} 20.0%, ${Colors.Green500} 20.0% 40.0%, ${Colors.Blue500} 40.0% 60.0%, ${Colors.Blue200} 60.0% 80.0%, ${Colors.Blue200} 80.0%)`,
    );
  });
});
