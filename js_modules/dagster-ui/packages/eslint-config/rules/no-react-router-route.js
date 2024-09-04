const {findRelativeImportPath} = require('../util/findRelativeImportPath');

const {ESLintUtils, AST_NODE_TYPES} = require('@typescript-eslint/utils');

const createRule = ESLintUtils.RuleCreator((name) => name);

module.exports = createRule({
  create(context) {
    return {
      [AST_NODE_TYPES.ImportDeclaration](node) {
        if (context.getFilename().endsWith('/ui-core/src/app/Route.tsx')) {
          return;
        }
        if (
          node.source.value === 'react-router-dom' &&
          node.specifiers.some((specifier) => specifier.imported.name === 'Route')
        ) {
          context.report({
            node,
            messageId: 'useDagsterRoute',
            fix(fixer) {
              const routeSpecifier = node.specifiers.find(
                (specifier) => specifier.imported.name === 'Route',
              );
              const importRange = [node.range[0], node.range[1]];
              const routeRange = [routeSpecifier.range[0], routeSpecifier.range[1]];

              const currentFilePath = context.getFilename();
              let relativeImportPath = findRelativeImportPath(currentFilePath, 'src/app/Route.tsx');

              if (!relativeImportPath) {
                relativeImportPath = '@dagster-io/ui-core/app/Route';
              } else if (!relativeImportPath.endsWith('Route')) {
                relativeImportPath = `${relativeImportPath}/Route`;
              }

              const newImport = `import { Route } from '${relativeImportPath}';\n`;

              const fixes = [];

              if (node.specifiers.length === 1) {
                // Remove the entire import statement if it only imports `Route`
                fixes.push(fixer.remove(node));
              } else {
                // Check if the specifier to remove is at the start or end
                if (routeSpecifier === node.specifiers[0]) {
                  // Remove the specifier and the following comma
                  fixes.push(fixer.removeRange([routeRange[0], node.specifiers[1].range[0]]));
                } else if (routeSpecifier === node.specifiers[node.specifiers.length - 1]) {
                  // Remove the preceding comma and the specifier
                  fixes.push(
                    fixer.removeRange([
                      node.specifiers[node.specifiers.length - 2].range[1],
                      routeRange[1],
                    ]),
                  );
                } else {
                  // Remove the specifier and the comma before it
                  fixes.push(
                    fixer.removeRange([
                      node.specifiers[node.specifiers.indexOf(routeSpecifier) - 1].range[1],
                      routeRange[1],
                    ]),
                  );
                }
              }

              // Insert the new import statement
              fixes.push(fixer.insertTextBeforeRange(node.range, newImport));

              return fixes;
            },
          });
        }
      },
    };
  },
  meta: {
    type: 'suggestion',
    docs: {
      description:
        'Disallow importing "Route" from "react-router-dom" and autofix to import from "@dagster-io/ui-core/Route"',
      category: 'Best Practices',
      recommended: true,
    },
    fixable: 'code',
    messages: {
      useDagsterRoute:
        'Import "Route" from "@dagster-io/ui-core/Route" instead of "react-router-dom".',
    },
    schema: [], // no options
  },
  defaultOptions: [],
});
