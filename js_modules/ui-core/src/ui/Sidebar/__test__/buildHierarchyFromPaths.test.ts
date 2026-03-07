/* eslint-disable jest/expect-expect */
import {buildHierarchyFromPaths} from '../buildHierarchyFromPaths';
import {HierarchyNode} from '../types';

/**
 * Renders hierarchy tree to a string representation for easier test assertions
 * Format: "📁 folder_name (path)" for folders, "📄 file_name (path)" for files
 * Indentation shows nesting level
 */
function renderTreeToString(nodes: HierarchyNode[], indent = 0): string {
  return nodes
    .map((node) => {
      const prefix = '  '.repeat(indent);
      const icon = node.type === 'folder' ? '📁' : '📄';
      const line = `${prefix}${icon} ${node.name} (${node.path})`;

      if (node.type === 'folder' && node.children.length > 0) {
        return line + '\n' + renderTreeToString(node.children, indent + 1);
      }
      return line;
    })
    .join('\n');
}

function expectTreeStructure(actual: HierarchyNode[], expected: string) {
  const actualString = renderTreeToString(actual);
  expect(actualString).toBe(expected.trim());
}

describe('buildHierarchyFromPaths', () => {
  describe('basic functionality', () => {
    it('builds hierarchy from simple paths', () => {
      const paths = ['aws/prod/database', 'aws/staging/database'];
      const result = buildHierarchyFromPaths(paths, false);

      expectTreeStructure(
        result,
        `
        📁 aws (aws)
          📁 prod (aws/prod)
          📁 staging (aws/staging)
      `,
      );
    });

    it('includes file nodes when includeFiles is true', () => {
      const paths = ['aws/prod/database', 'aws/staging/database'];
      const result = buildHierarchyFromPaths(paths, true);

      expectTreeStructure(
        result,
        `
        📁 aws (aws)
          📁 prod (aws/prod)
            📄 database (aws/prod/database)
          📁 staging (aws/staging)
            📄 database (aws/staging/database)
      `,
      );
    });

    it('excludes file nodes when includeFiles is false', () => {
      const paths = ['aws/database', 'gcp/database'];
      const result = buildHierarchyFromPaths(paths, false);

      expectTreeStructure(
        result,
        `
        📁 aws (aws)
        📁 gcp (gcp)
      `,
      );
    });
  });

  describe('sorting behavior', () => {
    it('sorts folders before files', () => {
      const paths = ['root/file1', 'root/folder1/file2'];
      const result = buildHierarchyFromPaths(paths, true);

      expectTreeStructure(
        result,
        `
        📁 root (root)
          📁 folder1 (root/folder1)
            📄 file2 (root/folder1/file2)
          📄 file1 (root/file1)
      `,
      );
    });

    it('sorts items alphabetically within type groups', () => {
      const paths = ['root/zebra', 'root/apple', 'root/beta/file', 'root/alpha/file'];
      const result = buildHierarchyFromPaths(paths, true);

      expectTreeStructure(
        result,
        `
        📁 root (root)
          📁 alpha (root/alpha)
            📄 file (root/alpha/file)
          📁 beta (root/beta)
            📄 file (root/beta/file)
          📄 apple (root/apple)
          📄 zebra (root/zebra)
      `,
      );
    });

    it('sorts numerically when paths contain numbers', () => {
      const paths = ['item1', 'item10', 'item2'];
      const result = buildHierarchyFromPaths(paths, true);

      expect(result.map((item) => item.name)).toEqual(['item1', 'item2', 'item10']);
    });
  });

  describe('edge cases', () => {
    it('handles empty paths array', () => {
      const result = buildHierarchyFromPaths([], false);
      expect(result).toEqual([]);
    });

    it('handles single root-level path', () => {
      const paths = ['root'];
      const result = buildHierarchyFromPaths(paths, true);

      expect(result).toEqual([
        {
          type: 'file',
          name: 'root',
          path: 'root',
        },
      ]);
    });

    it('handles single root-level path with includeFiles false', () => {
      const paths = ['root'];
      const result = buildHierarchyFromPaths(paths, false);

      expect(result).toEqual([]);
    });

    it('handles paths with no common root', () => {
      const paths = ['aws/database', 'gcp/storage', 'azure/compute'];
      const result = buildHierarchyFromPaths(paths, false);

      expectTreeStructure(
        result,
        `
        📁 aws (aws)
        📁 azure (azure)
        📁 gcp (gcp)
      `,
      );
    });

    it('handles deeply nested paths', () => {
      const paths = ['a/b/c/d/e/f'];
      const result = buildHierarchyFromPaths(paths, true);

      expectTreeStructure(
        result,
        `
        📁 a (a)
          📁 b (a/b)
            📁 c (a/b/c)
              📁 d (a/b/c/d)
                📁 e (a/b/c/d/e)
                  📄 f (a/b/c/d/e/f)
      `,
      );
    });

    it('handles duplicate paths', () => {
      const paths = ['aws/database', 'aws/database', 'gcp/storage'];
      const result = buildHierarchyFromPaths(paths, true);

      expectTreeStructure(
        result,
        `
        📁 aws (aws)
          📄 database (aws/database)
        📁 gcp (gcp)
          📄 storage (gcp/storage)
      `,
      );
    });

    it('handles paths with special characters', () => {
      const paths = ['aws/prod-us/my_database', 'aws/staging.env/test-db'];
      const result = buildHierarchyFromPaths(paths, true);

      expectTreeStructure(
        result,
        `
        📁 aws (aws)
          📁 prod-us (aws/prod-us)
            📄 my_database (aws/prod-us/my_database)
          📁 staging.env (aws/staging.env)
            📄 test-db (aws/staging.env/test-db)
      `,
      );
    });
  });

  describe('complex hierarchies', () => {
    it('builds complex multi-level hierarchy', () => {
      const paths = [
        'aws/prod/database/users',
        'aws/prod/database/orders',
        'aws/staging/cache/redis',
        'gcp/prod/storage/images',
        'gcp/dev/compute/workers',
      ];
      const result = buildHierarchyFromPaths(paths, true);

      expectTreeStructure(
        result,
        `
        📁 aws (aws)
          📁 prod (aws/prod)
            📁 database (aws/prod/database)
              📄 orders (aws/prod/database/orders)
              📄 users (aws/prod/database/users)
          📁 staging (aws/staging)
            📁 cache (aws/staging/cache)
              📄 redis (aws/staging/cache/redis)
        📁 gcp (gcp)
          📁 dev (gcp/dev)
            📁 compute (gcp/dev/compute)
              📄 workers (gcp/dev/compute/workers)
          📁 prod (gcp/prod)
            📁 storage (gcp/prod/storage)
              📄 images (gcp/prod/storage/images)
      `,
      );
    });
  });
});
