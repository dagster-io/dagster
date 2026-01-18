import {
  extractKeyPrefixFromSelection,
  selectionReplacingKeyPrefix,
} from '../AssetCatalogTableSidebar';

describe('AssetCatalogTableSidebar', () => {
  describe('extractKeyPrefixFromSelection', () => {
    it('extracts key prefix from simple selection', () => {
      const result = extractKeyPrefixFromSelection('key:"aws/prod/*"');
      expect(result).toEqual({
        text: 'key:"aws/prod/*"',
        key: 'aws/prod',
      });
    });

    it('extracts key prefix with wildcard only', () => {
      const result = extractKeyPrefixFromSelection('key:"*"');
      expect(result).toEqual({
        text: 'key:"*"',
        key: '*',
      });
    });

    it('extracts key prefix from complex selection with AND', () => {
      const result = extractKeyPrefixFromSelection(
        'code_location:"dagster_open_platform" AND key:"aws/prod/*"',
      );
      expect(result).toEqual({
        text: 'key:"aws/prod/*"',
        key: 'aws/prod',
      });
    });

    it('returns null for selection without key prefix', () => {
      const result = extractKeyPrefixFromSelection('code_location:"dagster_open_platform"');
      expect(result).toBeNull();
    });

    it('returns null for selection with multiple key prefixes', () => {
      const result = extractKeyPrefixFromSelection('key:"aws/*" OR key:"gcp/*"');
      expect(result).toBeNull();
    });

    it('returns null for empty selection', () => {
      const result = extractKeyPrefixFromSelection('');
      expect(result).toBeNull();
    });
  });

  describe('selectionReplacingKeyPrefix', () => {
    it('replaces existing key prefix', () => {
      const result = selectionReplacingKeyPrefix('key:"aws/prod/*"', 'gcp/staging');
      expect(result).toBe('key:"gcp/staging/*"');
    });

    it('adds key prefix to empty selection', () => {
      const result = selectionReplacingKeyPrefix('', 'aws/prod');
      expect(result).toBe('key:"aws/prod/*"');
    });

    it('adds wildcard key prefix for empty next key prefix', () => {
      const result = selectionReplacingKeyPrefix('', '');
      expect(result).toBe('key:"*"');
    });

    it('adds key prefix to existing selection without key clause', () => {
      const result = selectionReplacingKeyPrefix('code_location:"dagster"', 'aws/prod');
      expect(result).toBe('code_location:"dagster" AND key:"aws/prod/*"');
    });

    it('adds parentheses around OR selection when adding key prefix', () => {
      const result = selectionReplacingKeyPrefix('tag:"env" OR tag:"prod"', 'aws/staging');
      expect(result).toBe('(tag:"env" OR tag:"prod") AND key:"aws/staging/*"');
    });

    it('does not add parentheses if selection already starts with parentheses', () => {
      const result = selectionReplacingKeyPrefix('(tag:"env" OR tag:"prod")', 'aws/staging');
      expect(result).toBe('(tag:"env" OR tag:"prod") AND key:"aws/staging/*"');
    });

    it('replaces existing key prefix in complex selection', () => {
      const result = selectionReplacingKeyPrefix(
        'code_location:"dagster" AND key:"aws/prod/*"',
        'gcp/staging',
      );
      expect(result).toBe('code_location:"dagster" AND key:"gcp/staging/*"');
    });

    it('replaces key prefix with wildcard when nextKeyPrefix is empty', () => {
      const result = selectionReplacingKeyPrefix('key:"aws/prod/*"', '');
      expect(result).toBe('key:"*"');
    });

    it('handles case-insensitive OR detection', () => {
      const result = selectionReplacingKeyPrefix('tag:"env" or tag:"prod"', 'aws/staging');
      expect(result).toBe('(tag:"env" or tag:"prod") AND key:"aws/staging/*"');
    });
  });
});
