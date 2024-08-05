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
              const absolutePath = path.relative(
                context.getCwd(),
                path.resolve(path.dirname(context.getFilename()), node.source.value),
              );
              return fixer.replaceText(node.source, `'${absolutePath}'`);
            },
          });
        }
      },
      CallExpression(node) {
        if (
          node.callee.type === 'Import' &&
          node.arguments[0] &&
          node.arguments[0].type === 'Literal' &&
          node.arguments[0].value.endsWith('.oss') &&
          node.arguments[0].value.startsWith('.')
        ) {
          context.report({
            node,
            message: 'Relative dynamic importing files that end with ".oss.tsx" is not allowed.',
            fix: (fixer) => {
              const absolutePath = path.relative(
                context.getCwd(),
                path.resolve(path.dirname(context.getFilename()), node.arguments[0].value),
              );
              return fixer.replaceText(node.arguments[0], `'${absolutePath}'`);
            },
          });
        }
      },
    };
  },
};
