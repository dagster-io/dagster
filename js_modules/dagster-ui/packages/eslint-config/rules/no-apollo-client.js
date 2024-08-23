/* eslint-disable */

const fs = require('fs');
const path = require('path');

module.exports = {
  meta: {
    type: 'suggestion',
    fixable: 'code', // This marks the rule as auto-fixable
    messages: {
      useWrappedApolloClient:
        'Please use our wrapped apollo-client module which includes performance instrumentation.',
    },
  },
  create(context) {
    return {
      ImportDeclaration(node) {
        if (context.getFilename().endsWith('/apollo-client')) {
          return;
        }
        if (node.source.value === '@apollo/client') {
          context.report({
            node,
            messageId: 'useWrappedApolloClient',
            fix(fixer) {
              const currentFilePath = context.getFilename();
              const relativeImportPath = findRelativeImportPath(
                currentFilePath,
                'src/apollo-client',
                'index.tsx',
              );

              return fixer.replaceText(node.source, `'${relativeImportPath}'`);
            },
          });
        }
      },
    };
  },
};

function findRelativeImportPath(currentFilePath, targetDirName, targetFileName) {
  let currentDir = path.dirname(currentFilePath);

  while (currentDir !== path.parse(currentDir).root) {
    const srcPath = path.join(currentDir, targetDirName);
    const targetFilePath = path.join(srcPath, targetFileName);

    if (fs.existsSync(targetFilePath)) {
      return path.relative(path.dirname(currentFilePath), srcPath);
    }

    currentDir = path.dirname(currentDir);
  }

  // If we can't find the file then it means we're not in the ui-core package (we might be in cloud) so
  // grab the import from @dagster-io/ui-core.

  return '@dagster-io/ui-core/apollo-client';
}
