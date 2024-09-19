import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

// todo dish: Delete this in favor of `makeAutomationKey`, they're the same.
export const makeSensorKey = (repoAddress: RepoAddress, sensorName: string) => {
  return `${repoAddressAsHumanString(repoAddress)}-${sensorName}`;
};

export const makeAutomationKey = (repoAddress: RepoAddress, automationName: string) => {
  return `${repoAddressAsHumanString(repoAddress)}-${automationName}`;
};
