import * as ts from 'typescript';

import {UNSAFE_BROWSER_APIS, UNSAFE_IMPORTS} from './types';

/**
 * Checks if a node is within a safety check (like typeof window !== 'undefined')
 */
export function isInSafetyCheck(node: ts.Node, apiName: string): boolean {
  let parent = node.parent;
  let depth = 0;
  const maxDepth = 10;

  while (parent && depth < maxDepth) {
    // Check for if statements with typeof checks
    if (ts.isIfStatement(parent)) {
      const condition = parent.expression;
      if (ts.isBinaryExpression(condition)) {
        const {left, operatorToken, right} = condition;
        if (
          (operatorToken.kind === ts.SyntaxKind.ExclamationEqualsEqualsToken ||
            operatorToken.kind === ts.SyntaxKind.ExclamationEqualsToken) &&
          ts.isTypeOfExpression(left) &&
          ts.isStringLiteral(right) &&
          right.text === 'undefined'
        ) {
          if (ts.isIdentifier(left.expression)) {
            const checkedVariable = left.expression.getText();
            return checkedVariable === apiName;
          }
        }
      }
    }

    // Check for ternary expressions with typeof checks
    if (ts.isConditionalExpression(parent)) {
      const condition = parent.condition;
      if (ts.isBinaryExpression(condition)) {
        const {left, operatorToken, right} = condition;
        if (
          (operatorToken.kind === ts.SyntaxKind.ExclamationEqualsEqualsToken ||
            operatorToken.kind === ts.SyntaxKind.ExclamationEqualsToken) &&
          ts.isTypeOfExpression(left) &&
          ts.isStringLiteral(right) &&
          right.text === 'undefined'
        ) {
          if (ts.isIdentifier(left.expression)) {
            const checkedVariable = left.expression.getText();
            if (
              checkedVariable === apiName &&
              parent.whenTrue.getFullText().includes(node.getFullText())
            ) {
              return true;
            }
          }
        }
      }
    }

    // Check for logical AND patterns like: window && window.something
    if (
      ts.isBinaryExpression(parent) &&
      parent.operatorToken.kind === ts.SyntaxKind.AmpersandAmpersandToken
    ) {
      // For now, return true for any && pattern - could be made more specific
      return true;
    }

    parent = parent.parent;
    depth++;
  }

  return false;
}

/**
 * Checks if an identifier is a direct global reference (not a property name, type annotation, etc.)
 */
export function isDirectGlobalReference(node: ts.Node): boolean {
  if (!ts.isIdentifier(node)) {
    return false;
  }

  const parent = node.parent;
  if (!parent) {
    return true;
  }

  // Not a direct reference if it's a property name in member access
  if (ts.isPropertyAccessExpression(parent) && parent.name === node) {
    return false;
  }

  // Not a direct reference if it's in an object literal property
  if (ts.isPropertyAssignment(parent) && parent.name === node) {
    return false;
  }

  // Not a direct reference if it's a property signature in interface/type
  if (ts.isPropertySignature(parent) && parent.name === node) {
    return false;
  }

  // Not a direct reference if it's a type annotation
  if (ts.isTypeReferenceNode(parent)) {
    return false;
  }

  // Not a direct reference if it's part of a qualified name (e.g., dagre.Node)
  if (ts.isQualifiedName(parent) && parent.right === node) {
    return false;
  }

  // Not a direct reference if it's the right side of a property access in a type context
  if (ts.isPropertyAccessExpression(parent) && parent.name === node) {
    let typeContext = parent.parent;
    while (typeContext) {
      if (ts.isTypeReferenceNode(typeContext) || ts.isTypeNode(typeContext)) {
        return false;
      }
      if (ts.isVariableDeclaration(typeContext) || ts.isPropertySignature(typeContext)) {
        return false;
      }
      typeContext = typeContext.parent;
    }
  }

  // Not a direct reference if it's being declared as a variable/parameter
  if (ts.isVariableDeclaration(parent) && parent.name === node) {
    return false;
  }

  if (ts.isParameter(parent) && parent.name === node) {
    return false;
  }

  return true;
}

/**
 * Checks if an identifier is shadowed by a local variable or parameter
 */
export function isIdentifierShadowed(node: ts.Identifier): boolean {
  const identifierName = node.getText();
  let current: ts.Node | undefined = node;

  while (current) {
    // Check for function parameters
    if (
      ts.isFunctionDeclaration(current) ||
      ts.isFunctionExpression(current) ||
      ts.isArrowFunction(current) ||
      ts.isMethodDeclaration(current)
    ) {
      for (const param of current.parameters) {
        if (ts.isIdentifier(param.name) && param.name.getText() === identifierName) {
          return true;
        }
      }
    }

    // Check for variable declarations in the same scope
    if (ts.isBlock(current)) {
      for (const statement of current.statements) {
        if (ts.isVariableStatement(statement)) {
          for (const declaration of statement.declarationList.declarations) {
            if (
              ts.isIdentifier(declaration.name) &&
              declaration.name.getText() === identifierName
            ) {
              return true; // Found a variable declaration with the same name
            }
          }
        } else if (ts.isFunctionDeclaration(statement) && statement.name) {
          if (statement.name.getText() === identifierName) {
            return true; // Found a function declaration with the same name
          }
        }
      }
    }

    current = current.parent;
  }

  return false; // No local declaration found, might be a global reference
}

/**
 * Analyzes a source file and finds unsafe API usages
 */
export function findUnsafeApiUsages(
  sourceFile: ts.SourceFile,
  _filePath: string,
): Array<{node: ts.Node; api: string; type: 'api' | 'import'}> {
  const usages: Array<{node: ts.Node; api: string; type: 'api' | 'import'}> = [];

  function visitNode(node: ts.Node) {
    // Check for unsafe imports
    if (
      ts.isImportDeclaration(node) &&
      node.moduleSpecifier &&
      ts.isStringLiteral(node.moduleSpecifier)
    ) {
      const moduleName = node.moduleSpecifier.text;
      if (UNSAFE_IMPORTS.has(moduleName) || moduleName.startsWith('react/')) {
        usages.push({
          node,
          api: `import ${moduleName}`,
          type: 'import',
        });
      }
    }

    // Check for unsafe browser API usage
    if (ts.isIdentifier(node)) {
      const apiName = node.getText();
      if (UNSAFE_BROWSER_APIS.has(apiName)) {
        // Check if this is a direct global reference
        if (isDirectGlobalReference(node)) {
          // Check if the identifier is shadowed
          if (!isIdentifierShadowed(node)) {
            // Check if it's within a safety check
            if (!isInSafetyCheck(node, apiName)) {
              usages.push({
                node,
                api: apiName,
                type: 'api',
              });
            }
          }
        }
      }
    }

    ts.forEachChild(node, visitNode);
  }

  visitNode(sourceFile);
  return usages;
}

/**
 * Generates appropriate error message for unsafe API usage
 */
export function generateErrorMessage(api: string, type: 'api' | 'import'): string {
  if (type === 'import') {
    const importName = api.replace('import ', '');
    let message = `${importName} should not be imported in worker context`;
    if (importName === 'react' || importName.startsWith('react/')) {
      message += ' (increases bundle size and not needed in workers)';
    } else if (importName === '@apollo/client') {
      message += ' (GraphQL client not needed in workers)';
    }
    return message;
  }

  // API usage messages
  switch (api) {
    case 'requestAnimationFrame':
    case 'cancelAnimationFrame':
      return `${api} is not available in worker context (use setTimeout/setInterval instead)`;
    case 'navigator':
      return `${api} is not available in worker context (access userAgent from worker context instead)`;
    case 'location':
      return `${api} is not available in worker context (use self.location in worker if needed)`;
    case 'localStorage':
    case 'sessionStorage':
      return `${api} is not available in worker context (use IndexedDB or pass data from main thread)`;
    case 'alert':
    case 'confirm':
    case 'prompt':
      return `${api} is not available in worker context (communicate with main thread instead)`;
    default:
      return `${api} is not available in worker context`;
  }
}
