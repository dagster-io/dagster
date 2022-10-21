import {repoAddressAsString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

interface Bucket {
  repoAddress: RepoAddress;
}

export const sortRepoBuckets = <B extends Bucket>(buckets: B[]) => {
  return [...buckets].sort((a, b) => {
    const aString = repoAddressAsString(a.repoAddress);
    const bString = repoAddressAsString(b.repoAddress);
    return aString.localeCompare(bString);
  });
};
