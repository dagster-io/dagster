import {RepoAddress} from '../workspace/types';

export interface Config {
  repoAddress: RepoAddress;
  sensorName: string;
}

export const useSensorAlertDetails = (_config: Config) => null;
