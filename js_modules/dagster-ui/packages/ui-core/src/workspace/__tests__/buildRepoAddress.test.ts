import {
  buildRepoAddress,
  buildRepoPathForHuman,
  buildRepoPathForURL,
  DUNDER_REPO_NAME,
} from '../buildRepoAddress';

describe('Repo address utilities', () => {
  describe('buildRepoAddress', () => {
    it('creates a RepoAddress object', () => {
      expect(buildRepoAddress('foo', 'bar')).toEqual({
        name: 'foo',
        location: 'bar',
      });
    });

    it('memoizes based on the name/location', () => {
      const repoAddress = buildRepoAddress('foo', 'bar');
      expect(buildRepoAddress('foo', 'bar')).toBe(repoAddress);
    });
  });

  describe('buildRepoPathForHuman', () => {
    it('renders a legible repo path', () => {
      expect(buildRepoPathForHuman('foo', 'bar')).toBe('foo@bar');
      expect(buildRepoPathForHuman('foo_repo', 'bar_location')).toBe('foo_repo@bar_location');
      expect(buildRepoPathForHuman('foo', 'location:with:colons')).toBe('foo@location:with:colons');
    });

    it('omits the dunder repo name', () => {
      expect(buildRepoPathForHuman(DUNDER_REPO_NAME, 'bar')).toBe('bar');
    });
  });

  describe('buildRepoPathForURL', () => {
    it('renders a repo path for URLs', () => {
      expect(buildRepoPathForURL('foo', 'bar')).toBe('foo@bar');
      expect(buildRepoPathForURL('foo_repo', 'bar_location')).toBe('foo_repo@bar_location');
    });

    it('URI-encodes characters in location name', () => {
      expect(buildRepoPathForURL('foo', 'location:with:colons')).toBe(
        'foo@location%3Awith%3Acolons',
      );
      expect(buildRepoPathForURL('foo', 'location/with/slashes')).toBe(
        'foo@location%2Fwith%2Fslashes',
      );
    });

    it('omits the dunder repo name', () => {
      expect(buildRepoPathForURL(DUNDER_REPO_NAME, 'bar')).toBe('bar');
    });
  });
});
