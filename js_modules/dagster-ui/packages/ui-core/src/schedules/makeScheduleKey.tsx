import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

export const makeScheduleKey = (repoAddress: RepoAddress, scheduleName: string) => {
  return `${repoAddressAsHumanString(repoAddress)}-${scheduleName}`;
};
