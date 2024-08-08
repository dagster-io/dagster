/* eslint-disable */

const path = require('path');

module.exports = {
  meta: {
    type: 'problem',
    docs: {
      description:
        'disallow relative importing files that end with ".oss" and autofix to absolute path',
      category: 'Best Practices',
      recommended: false,
    },
    fixable: 'code',
    schema: [], // no options
  },
  create(context) {
    return {
      ImportDeclaration(node) {
        if (node.source.value.endsWith('.oss') && node.source.value.startsWith('.')) {
          context.report({
            node,
            message: 'Relative importing files that end with ".oss" is not allowed.',
            fix: (fixer) => {
              const absolutePath = path
                .relative(
                  context.getCwd(),
                  path.resolve(path.dirname(context.getFilename()), node.source.value),
                )
                .replace(/^src/, 'shared');
              return fixer.replaceText(node.source, `'${absolutePath}'`);
            },
          });
        }
      },
      ImportExpression(node) {
        if (node.source.value.endsWith('.oss') && node.source.value.startsWith('.')) {
          context.report({
            node,
            message: 'Relative dynamic importing files that end with ".oss.tsx" is not allowed.',
            fix: (fixer) => {
              const absolutePath = path
                .relative(
                  context.getCwd(),
                  path.resolve(path.dirname(context.getFilename()), node.source.value),
                )
                .replace(/^src/, 'shared');
              return fixer.replaceText(node.source, `'${absolutePath}'`);
            },
          });
        }
      },
    };
  },
};
