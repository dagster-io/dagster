import {assertUnreachable} from '../app/Util';
import {RowObjectType, RunAutomation, TimelineRow} from '../runs/RunTimelineTypes';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

export const groupRunsByAutomation = (jobRows: TimelineRow[]): TimelineRow[] => {
  const byAutomation: Record<string, TimelineRow> = {};
  for (const jobRow of jobRows) {
    const {repoAddress, runs} = jobRow;
    runs.forEach((run) => {
      const {automation} = run;
      const key = makeAutomationKey(repoAddress, automation);

      if (!byAutomation[key]) {
        const name = automationName(automation);
        byAutomation[key] = {
          key,
          name,
          type: automation?.type || 'manual',
          path: makeAutomationPath(repoAddress, automation?.type, name),
          repoAddress,
          runs: [],
        };
      }

      byAutomation[key]!.runs.push(run);
    });
  }

  return Object.values(byAutomation);
};

const automationName = (automation: RunAutomation | null) => {
  if (!automation) {
    return 'Launched manually';
  }

  const {type} = automation;
  switch (type) {
    case 'legacy-amp':
      return 'Automation condition';
    case 'schedule':
    case 'sensor':
      return automation.name;
    default:
      return assertUnreachable(type);
  }
};

const makeAutomationKey = (repoAddress: RepoAddress, automation: RunAutomation | null) => {
  const repo = repoAddressAsHumanString(repoAddress);
  if (!automation) {
    return `MANUAL-${repo}`;
  }

  const {type} = automation;
  switch (type) {
    case 'legacy-amp':
      return `AMP-${repo}`;
    case 'schedule':
    case 'sensor':
      return `${automation.name}-${type}-${repo}`;
    default:
      return assertUnreachable(type);
  }
};

const makeAutomationPath = (repoAddress: RepoAddress, type?: RowObjectType, name?: string) => {
  if (type === 'schedule') {
    return workspacePathFromAddress(repoAddress, `/schedules/${name}`);
  }
  if (type === 'sensor') {
    return workspacePathFromAddress(repoAddress, `/sensors/${name}`);
  }
  return '';
};
