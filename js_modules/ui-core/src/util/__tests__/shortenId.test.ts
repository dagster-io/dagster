import {shortenId} from '../shortenId';

describe('shortenId', () => {
  test('keeps the first eight characters of a long id', () => {
    expect(shortenId('f3a1b2c4-5d6e-7f80-9a1b-2c3d4e5f6a7b')).toBe('f3a1b2c4');
  });

  test('returns an id of eight characters or fewer unchanged', () => {
    expect(shortenId('f3a1b2c4')).toBe('f3a1b2c4');
    expect(shortenId('abc')).toBe('abc');
    expect(shortenId('')).toBe('');
  });
});
