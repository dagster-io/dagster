import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

interface Bucket {
  repoAddress: RepoAddress;
}

export const sortRepoBuckets = <B extends Bucket>(buckets: B[]) => {
  return [...buckets].sort((a, b) => {
    const aString = repoAddressAsHumanString(a.repoAddress);
    const bString = repoAddressAsHumanString(b.repoAddress);
    return aString.localeCompare(bString);
  });
};
