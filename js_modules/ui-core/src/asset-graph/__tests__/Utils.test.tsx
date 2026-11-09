import {buildMaterializationEvent, buildRun} from '../../graphql/builders';
import {RunStatus} from '../../graphql/types';
import {
  buildSVGPathHorizontal,
  buildSVGPathVertical,
  buildSVGPathWithBoundaryCorridors,
  shouldDisplayRunFailure,
  tokenForAssetKey,
  tokenToAssetKey,
} from '../Utils';

describe('SVG path builders', () => {
  it('builds a horizontal path with boundary corridors', () => {
    expect(
      buildSVGPathWithBoundaryCorridors(
        {
          from: {x: 10, y: 20},
          to: {x: 130, y: 80},
          sourceBoundary: 40,
          targetBoundary: 100,
        },
        'horizontal',
      ),
    ).toBe('M10,20L40,20C70,20 70,80 100,80L130,80');
  });

  it('builds a vertical path with boundary corridors', () => {
    expect(
      buildSVGPathWithBoundaryCorridors(
        {
          from: {x: 20, y: 10},
          to: {x: 80, y: 130},
          sourceBoundary: 40,
          targetBoundary: 100,
        },
        'vertical',
      ),
    ).toBe('M20,10L20,40C20,70 80,70 80,100L80,130');
  });

  it('keeps legacy path builders unchanged', () => {
    expect(buildSVGPathHorizontal({source: {x: 0, y: 0}, target: {x: 100, y: 50}})).toBe(
      'M0,0C50,0,50,50,100,50',
    );
    expect(buildSVGPathVertical({source: {x: 0, y: 0}, target: {x: 50, y: 100}})).toBe(
      'M0,0C0,50,50,50,50,100',
    );
  });
});

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
