const {findRelativeImportPath} = require('../util/findRelativeImportPath');
const {ESLintUtils, AST_NODE_TYPES} = require('@typescript-eslint/utils');
const createRule = ESLintUtils.RuleCreator((name) => name);

module.exports = createRule({
  create(context) {
    return {
      [AST_NODE_TYPES.ImportDeclaration](node) {
        if (context.getFilename().endsWith('/apollo-client/index.tsx')) {
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
                'src/apollo-client/index.tsx',
              );

              // If we can't find the file then it means we're not in the ui-core package (we might be in cloud) so
              // grab the import from @dagster-io/ui-core.
              return fixer.replaceText(
                node.source,
                `'${relativeImportPath ?? '@dagster-io/ui-core/apollo-client'}'`,
              );
            },
          });
        }
      },
    };
  },
  name: 'no-apollo-client',
  meta: {
    type: 'suggestion',
    fixable: 'code',
    messages: {
      useWrappedApolloClient:
        'Please use our wrapped apollo-client module which includes performance instrumentation.',
    },
  },
  defaultOptions: [],
});
