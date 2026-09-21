import {buildMaterializationEvent, buildRun} from '../../graphql/builders';
import {RunStatus} from '../../graphql/types';
import {shouldDisplayRunFailure, tokenForAssetKey, tokenToAssetKey} from '../Utils';

describe('shouldDisplayRunFailure', () => {
  it('should return false if the latest materialization is from the latest run', () => {
    expect(
      shouldDisplayRunFailure(
        buildRun({id: '1', status: RunStatus.FAILURE, endTime: 1673301346}),
        buildMaterializationEvent({runId: '1', timestamp: `1673300346000`}),
      ),
    ).toEqual(false);
  });
  it('should return false if the latest materialization is newer than the failure (manually reported event case)', () => {
    expect(
      shouldDisplayRunFailure(
        buildRun({id: '1', status: RunStatus.FAILURE, endTime: 1673301346}),
        buildMaterializationEvent({runId: undefined, timestamp: `1674400000000`}),
      ),
    ).toEqual(false);
  });
  it('should return false if the run succeeded', () => {
    expect(
      shouldDisplayRunFailure(
        buildRun({id: '2', status: RunStatus.SUCCESS, endTime: 1673301346}),
        buildMaterializationEvent({runId: '1', timestamp: `1673300346000`}),
      ),
    ).toEqual(false);
  });
  it('should return true if the latest run status is failed and other conditions are not met', () => {
    expect(
      shouldDisplayRunFailure(
        buildRun({id: '2', status: RunStatus.FAILURE, endTime: 1673301346}),
        buildMaterializationEvent({runId: '1', timestamp: `1673300000000`}),
      ),
    ).toEqual(true);
  });
});

describe('tokenForAssetKey / tokenToAssetKey', () => {
  it('produces distinct tokens for components with and without slashes', () => {
    expect(tokenForAssetKey({path: ['foo', 'bar']})).toBe('foo/bar');
    expect(tokenForAssetKey({path: ['foo/bar']})).toBe('foo\\/bar');
    expect(tokenForAssetKey({path: ['foo', 'bar']})).not.toBe(
      tokenForAssetKey({path: ['foo/bar']}),
    );
  });

  it('round-trips via tokenToAssetKey', () => {
    const cases: string[][] = [
      ['foo'],
      ['foo', 'bar'],
      ['foo/bar'],
      ['a', 'b/c', 'd'],
      ['a\\b'],
      ['', 'empty'],
    ];
    for (const path of cases) {
      expect(tokenToAssetKey(tokenForAssetKey({path})).path).toEqual(path);
    }
  });
});
