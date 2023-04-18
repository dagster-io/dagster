import {buildRepoAddress, DUNDER_REPO_NAME} from '../../workspace/buildRepoAddress';
import {repoAddressAsHumanString} from '../../workspace/repoAddressAsString';
import {sortRepoBuckets} from '../sortRepoBuckets';

describe('sortRepoBuckets', () => {
  it('does basic sorting properly', () => {
    const lorem = {repoAddress: buildRepoAddress('lorem', 'ipsum')};
    const dolorsit = {repoAddress: buildRepoAddress('dolorsit', 'amet')};
    const consectetur = {repoAddress: buildRepoAddress('consectetur', 'adipiscing')};
    const list = [lorem, dolorsit, consectetur];

    const sorted = sortRepoBuckets(list);

    // The input object is not mutated.
    expect(sorted).not.toBe(list);

    // Same repo bucket objects, sorted.
    expect(sorted).toEqual([consectetur, dolorsit, lorem]);
  });

  it('sorts by repo location when repo names are the same', () => {
    const newyork = {repoAddress: buildRepoAddress('lorem', 'newyork')};
    const chicago = {repoAddress: buildRepoAddress('lorem', 'chicago')};
    const boston = {repoAddress: buildRepoAddress('lorem', 'boston')};
    const list = [newyork, chicago, boston];

    const sorted = sortRepoBuckets(list);

    // Same repo bucket objects, sorted by repo location because repo names are all the same.
    expect(sorted).toEqual([boston, chicago, newyork]);
  });

  it('sorts by repo location when dunder repo names are used', () => {
    const newyork = {repoAddress: buildRepoAddress(DUNDER_REPO_NAME, 'newyork')};
    const chicago = {repoAddress: buildRepoAddress(DUNDER_REPO_NAME, 'chicago')};
    const boston = {repoAddress: buildRepoAddress('lorem', 'boston')};
    const list = [newyork, chicago, boston];

    const sorted = sortRepoBuckets(list);

    // Same repo bucket objects. Repo locations are used for sort order when dunder repo
    // names are used, which puts `chicago` ahead of `lorem@boston`.
    expect(sorted).toEqual([chicago, boston, newyork]);
  });

  it('sorts correctly with regard to capitalization and diacritics', () => {
    // Would be sorted after "lorem" because of `ä`, in spite of `a` being after `o`.
    const umlaut = {repoAddress: buildRepoAddress('lärem', 'ipsum')};

    // Would be sorted before "lorem" because of capital `L`, in spite of `u` being after `o`.
    const capitalizedWithU = {repoAddress: buildRepoAddress('Lurem', 'ipsum')};

    // Would be sorted before "lorem" because of capital `L`, in spite of `upsum` being after `ipsum`.
    const capitalizedWithO = {repoAddress: buildRepoAddress('Lorem', 'upsum')};

    const normal = {repoAddress: buildRepoAddress('lorem', 'ipsum')};
    const list = [umlaut, capitalizedWithU, capitalizedWithO, normal];

    // Sanity check default sorting, which does not give us the ideal result.
    expect(list.map(({repoAddress}) => repoAddressAsHumanString(repoAddress)).sort()).toEqual([
      'Lorem@upsum',
      'Lurem@ipsum',
      'lorem@ipsum',
      'lärem@ipsum',
    ]);
    const sorted = sortRepoBuckets(list);

    // Desired sort order:
    expect(sorted).toEqual([umlaut, normal, capitalizedWithO, capitalizedWithU]);
  });
});
