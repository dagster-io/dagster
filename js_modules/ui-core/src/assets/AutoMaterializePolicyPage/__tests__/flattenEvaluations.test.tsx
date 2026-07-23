import {
  assetKeyForEntityKey,
  buildEntityKey,
  displayNameForEntityKey,
  entityKeyMatches,
  tokenForEntityKey,
} from '../flattenEvaluations';
import {EntityKeyFragment} from '../types/GetEvaluationsQuery.types';

const assetKey: EntityKeyFragment = {__typename: 'AssetKey', path: ['foo', 'bar']};
const checkKey: EntityKeyFragment = {
  __typename: 'AssetCheckhandle',
  name: 'my_check',
  assetKey: {__typename: 'AssetKey', path: ['foo', 'bar']},
};
const jobKey: EntityKeyFragment = {__typename: 'AssetJobKey', jobName: 'my_job'};

describe('tokenForEntityKey', () => {
  it('tokenizes each entity key type distinctly', () => {
    expect(tokenForEntityKey(assetKey)).toBe('foo/bar');
    expect(tokenForEntityKey(checkKey)).toBe('my_check::foo/bar');
    expect(tokenForEntityKey(jobKey)).toBe('job:my_job');
  });
});

describe('displayNameForEntityKey', () => {
  it('displays the bare job name for job keys', () => {
    expect(displayNameForEntityKey(jobKey)).toBe('my_job');
  });

  it('displays asset and check names', () => {
    expect(displayNameForEntityKey(assetKey)).toBe('foo / bar');
    expect(displayNameForEntityKey(checkKey)).toBe('my_check (foo / bar)');
  });
});

describe('assetKeyForEntityKey', () => {
  it('returns the asset key for asset and check keys', () => {
    expect(assetKeyForEntityKey(assetKey)).toEqual(assetKey);
    expect(assetKeyForEntityKey(checkKey)).toEqual({__typename: 'AssetKey', path: ['foo', 'bar']});
  });

  it('returns null for job keys, which have no asset key', () => {
    expect(assetKeyForEntityKey(jobKey)).toBeNull();
  });
});

describe('entityKeyMatches', () => {
  it('matches job keys by job name', () => {
    expect(entityKeyMatches(jobKey, {__typename: 'AssetJobKey', jobName: 'my_job'})).toBe(true);
    expect(entityKeyMatches(jobKey, {__typename: 'AssetJobKey', jobName: 'other_job'})).toBe(false);
  });

  it('does not match job keys against other entity key types', () => {
    expect(entityKeyMatches(jobKey, assetKey)).toBe(false);
    expect(entityKeyMatches(jobKey, checkKey)).toBe(false);
  });
});

describe('buildEntityKey', () => {
  it('builds an asset key by default', () => {
    expect(buildEntityKey(['foo', 'bar'], undefined)).toEqual(assetKey);
  });

  it('builds a check handle when a check name is provided', () => {
    expect(buildEntityKey(['foo', 'bar'], 'my_check')).toEqual(checkKey);
  });

  it('builds a job key when a job name is provided', () => {
    expect(buildEntityKey([], undefined, 'my_job')).toEqual(jobKey);
  });

  it('prefers the job name over a check name when both are provided', () => {
    expect(buildEntityKey(['foo', 'bar'], 'my_check', 'my_job')).toEqual(jobKey);
  });
});
