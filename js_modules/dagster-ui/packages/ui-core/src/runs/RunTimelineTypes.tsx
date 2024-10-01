import {RunStatus} from '../graphql/types';
import {RepoAddress} from '../workspace/types';

export type RunAutomation =
  | {type: 'legacy-amp'}
  | {type: 'schedule' | 'sensor'; repoAddress: RepoAddress; name: string};

export type TimelineRun = {
  id: string;
  status: RunStatus | 'SCHEDULED';
  startTime: number;
  endTime: number;
  automation: null | RunAutomation;
};

export type RowObjectType = 'job' | 'asset' | 'schedule' | 'sensor' | 'legacy-amp' | 'manual';

export type TimelineRow = {
  key: string;
  repoAddress: RepoAddress;
  name: string;
  type: RowObjectType;
  path: string;
  runs: TimelineRun[];
};
