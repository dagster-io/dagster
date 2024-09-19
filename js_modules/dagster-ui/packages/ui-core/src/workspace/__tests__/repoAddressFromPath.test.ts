import {DUNDER_REPO_NAME} from '../buildRepoAddress';
import {repoAddressFromPath} from '../repoAddressFromPath';

describe('repoAddressFromPath', () => {
  it('returns null if empty string', () => {
    expect(repoAddressFromPath('')).toEqual(null);
  });

  it('builds a RepoAddress from a valid repo@location', () => {
    expect(repoAddressFromPath('foo@bar')).toEqual({
      name: 'foo',
      location: 'bar',
    });
  });

  it('builds a RepoAddress from a valid repo@location with encoded location', () => {
    expect(repoAddressFromPath('foo@bar%3Abaz')).toEqual({
      name: 'foo',
      location: 'bar:baz',
    });
    expect(repoAddressFromPath('foo@bar%2Fbaz')).toEqual({
      name: 'foo',
      location: 'bar/baz',
    });
  });

  it('builds a RepoAddress from a code location with a dunder repo name', () => {
    expect(repoAddressFromPath('bar')).toEqual({
      name: DUNDER_REPO_NAME,
      location: 'bar',
    });
    expect(repoAddressFromPath('bar%2Fbaz')).toEqual({
      name: DUNDER_REPO_NAME,
      location: 'bar/baz',
    });
  });
});
