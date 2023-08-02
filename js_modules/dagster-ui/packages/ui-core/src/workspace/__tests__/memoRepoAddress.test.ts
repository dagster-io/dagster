import {buildRepoAddress} from '../buildRepoAddress';

describe('buildRepoAddress', () => {
  it('returns the exact object for the same arguments', () => {
    const a = buildRepoAddress('foo', 'bar');
    const b = buildRepoAddress('foo', 'bar');
    expect(a).toBe(b);
    const c = buildRepoAddress('derp', 'baz');
    expect(c).not.toBe(a);
  });
});
