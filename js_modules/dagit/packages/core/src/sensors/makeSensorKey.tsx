import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

export const makeSensorKey = (repoAddress: RepoAddress, sensorName: string) => {
  return `${repoAddressAsHumanString(repoAddress)}-${sensorName}`;
};
