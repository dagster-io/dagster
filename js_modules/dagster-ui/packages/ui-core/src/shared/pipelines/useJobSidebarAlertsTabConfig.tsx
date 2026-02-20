import {RepoAddress} from '../../workspace/types';

export interface Config {
  repoAddress?: RepoAddress;
  jobName: string;
}

export const useJobSidebarAlertsTabConfig = (_: Config) => null;
