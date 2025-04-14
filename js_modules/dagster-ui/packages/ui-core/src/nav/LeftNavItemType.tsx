import {IconName} from '@dagster-io/ui-components';

import {
  WorkspaceRepositorySchedule,
  WorkspaceRepositorySensor,
} from '../workspace/WorkspaceContext/WorkspaceContext';
import {RepoAddress} from '../workspace/types';

export type LeftNavItemType = {
  name: string;
  isJob: boolean;
  leftIcon: IconName | 'airflow';
  label: React.ReactNode;
  path: string;
  repoAddress: RepoAddress;
  schedules: WorkspaceRepositorySchedule[];
  sensors: WorkspaceRepositorySensor[];
};
