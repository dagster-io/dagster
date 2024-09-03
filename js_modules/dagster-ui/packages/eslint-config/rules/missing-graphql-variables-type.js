/* eslint-disable */

const fs = require('fs');
const path = require('path');
const {ESLintUtils, AST_NODE_TYPES} = require('@typescript-eslint/utils');

const createRule = ESLintUtils.RuleCreator((name) => name);

/**
 * Strategy:
 *  1. Pass over all useQuery calls and append "Variables" to the identifierName of the first type
 *    -- eg: useQuery<SomeQuery>() --> SomeQueryVariables
 *  2. Check if "SomeQueryVariables" is exported from the file that "SomeQuery" is imported from.
 *  3. If it's not then continue
 *     If it is then check that the second type argument to useQuery is that SomeQueryVariables.
 *     If not then throw an error.
 *
 */

const apisRequiringVariableType = new Set([
  'useQuery',
  'useMutation',
  'useSubscription',
  'useLazyQuery',
]);

module.exports = createRule({
  create(context) {
    return {
      [AST_NODE_TYPES.CallExpression](node) {
        const callee = node.callee;
        if (callee.type !== 'Identifier') {
          return;
        }
        // if it's not a useQuery call then ignore
        if (!apisRequiringVariableType.has(callee.name)) {
          return;
        }
        const API = callee.name;
        const queryType =
          node.typeParameters && node.typeParameters.params && node.typeParameters.params[0];
        if (!queryType || queryType.type !== 'TSTypeReference') {
          return;
        }
        if (queryType.typeName.type !== 'Identifier') {
          return;
        }

        const queryName = queryType.typeName.name;
        const variablesName = queryName + 'Variables';
        const secondType = node.typeParameters.params[1];
        if (
          secondType &&
          secondType.type === 'TSTypeReference' &&
          secondType.typeName.type === 'Identifier' &&
          secondType.typeName.name === variablesName
        ) {
          return;
        }
        let queryImportSpecifier = null;
        const importDeclaration = context.getSourceCode().ast.body.find(
          (node) =>
            node.type === 'ImportDeclaration' &&
            node.specifiers.find((node) => {
              if (node.type === 'ImportSpecifier' && node.local.name === queryName) {
                queryImportSpecifier = node;
                return true;
              }
            }),
        );
        if (!importDeclaration) {
          return;
        }
        context.report({
          messageId: 'missing-graphql-variables-type',
          node,
          data: {
            queryType: queryName,
            variablesType: variablesName,
            api: API,
          },
          *fix(fixer) {
            if (
              !importDeclaration.specifiers.find(
                (node) => node.type === 'ImportSpecifier' && node.local.name === variablesName,
              )
            ) {
              yield fixer.insertTextAfter(queryImportSpecifier, `, ${variablesName}`);
            }
            yield fixer.insertTextAfter(queryType, `, ${variablesName}`);
          },
        });
      },
    };
  },
  name: 'missing-graphql-variables-type',
  meta: {
    fixable: true,
    docs: {
      description: 'useQuery is missing QueryVariables parameter.',
      recommended: 'error',
    },
    messages: {
      'missing-graphql-variables-type':
        '`{{api}}<{{queryType}}>(...)` should be `{{api}}<{{queryType}},{{variablesType}}>(...)`.',
    },
    type: 'problem',
    schema: [],
  },
  defaultOptions: [],
});
