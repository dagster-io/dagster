const {ESLintUtils, AST_NODE_TYPES} = require('@typescript-eslint/utils');

const createRule = ESLintUtils.RuleCreator((name) => name);

module.exports = createRule({
  meta: {
    type: 'problem',
    docs: {
      description:
        'Disallow importing files using the shared/ path when the import does not end with ".oss"',
      category: 'Best Practices',
      recommended: false,
    },
    messages: {
      invalidSharedImport:
        'Imports using the "shared/" path must reference an import ending with ".oss"',
    },
    fixable: 'code', // Enable autofixing
    schema: [], // no options
  },
  defaultOptions: [],
  create: function create(context) {
    const path = require('path');

    /**
     * Converts a shared import path to a relative path based on the current file.
     * @param {string} importPath - The original import path starting with 'shared/'.
     * @returns {string} - The corrected relative import path.
     */
    function convertToRelativePath(importPath) {
      // Remove the 'shared/' prefix
      const targetPath = importPath.replace(/^shared\//, '');
      // Resolve the absolute path of the target file
      const absoluteTargetPath = path.resolve(__dirname, '../../ui-core/src/', targetPath);
      // Get the directory of the current file
      const currentDir = path.dirname(context.getFilename());
      // Compute the relative path from the current file to the target file
      let relativePath = path.relative(currentDir, absoluteTargetPath);
      // Ensure the relative path starts with './' or '../'
      if (!relativePath.startsWith('.')) {
        relativePath = `./${relativePath}`;
      }
      // Replace Windows backslashes with POSIX forward slashes
      return relativePath.replace(/\\/g, '/');
    }

    /**
     * Checks if the import path starts with 'shared/' and does not end with a valid suffix.
     * If so, reports an error and provides a fix to convert to a relative import.
     * @param {string} importPath - The path of the import.
     * @param {ASTNode} node - The AST node representing the import.
     * @returns {void}
     */
    function checkSharedImport(importPath, node) {
      if (typeof importPath !== 'string') {
        return;
      }

      if (importPath.startsWith('shared/')) {
        const validSuffixRegex = /\.oss$/;
        if (!validSuffixRegex.test(importPath)) {
          context.report({
            node,
            messageId: 'invalidSharedImport',
            fix: (fixer) => {
              const relativeImport = convertToRelativePath(importPath);
              return fixer.replaceText(node.source, `'${relativeImport}'`);
            },
          });
        }
      }

      if (importPath.startsWith('js_modules/dagster-ui/packages/ui-core/src')) {
        context.report({
          node,
          messageId: 'invalidSharedImport',
          fix: (fixer) => {
            return fixer.replaceText(
              node.source,
              `'${importPath.replace('js_modules/dagster-ui/packages/ui-core/src', 'shared')}'`,
            );
          },
        });
      }
    }

    return {
      [AST_NODE_TYPES.ImportDeclaration](node) {
        checkSharedImport(node.source.value, node);
      },
      [AST_NODE_TYPES.ImportExpression](node) {
        if (node.source && node.source.type === AST_NODE_TYPES.Literal) {
          checkSharedImport(node.source.value, node);
        }
      },
    };
  },
});
