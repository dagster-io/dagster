import {IconName} from '@dagster-io/ui';

import {
  WorkspaceRepositorySchedule,
  WorkspaceRepositorySensor,
} from '../workspace/WorkspaceContext';
import {RepoAddress} from '../workspace/types';

export type LeftNavItemType = {
  name: string;
  isJob: boolean;
  leftIcon: IconName;
  label: React.ReactNode;
  path: string;
  repoAddress: RepoAddress;
  schedules: WorkspaceRepositorySchedule[];
  sensors: WorkspaceRepositorySensor[];
};
