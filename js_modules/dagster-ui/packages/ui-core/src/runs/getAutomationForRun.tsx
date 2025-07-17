import {DagsterTag} from './RunTag';
import {RunAutomation} from './RunTimelineTypes';
import {RunTimelineFragment} from './types/useRunsForTimeline.types';
import {RepoAddress} from '../workspace/types';

export const getAutomationForRun = (
  repoAddress: RepoAddress,
  run: RunTimelineFragment,
): RunAutomation | null => {
  const {tags = []} = run;
  // First check for schedules or sensors
  for (const tag of tags) {
    if (tag.key === DagsterTag.ScheduleName) {
      return {type: 'schedule', repoAddress, name: tag.value};
    }
    if (tag.key === DagsterTag.SensorName) {
      return {type: 'sensor', repoAddress, name: tag.value};
    }
  }

  // Then check if it was launched by an automation condition without a sensor
  for (const tag of tags) {
    if (tag.key === DagsterTag.Automaterialize) {
      return {type: 'legacy-amp'};
    }
  }

  return null;
};
