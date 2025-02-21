import {RepoAddress} from '../workspace/types';

export interface Config {
  repoAddress: RepoAddress;
  scheduleName: string;
}

export const useScheduleAlertDetails = (_config: Config) => null;
