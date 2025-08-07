#!/usr/bin/env tsx

import * as path from 'path';

import {glob} from 'glob';
import * as ts from 'typescript';

// Browser APIs that are not available in worker contexts
const UNSAFE_BROWSER_APIS = new Set([
  // Global objects
  'window',
  'document',
  'navigator',

  // DOM-related globals
  'Element',
  'HTMLElement',
  'Node',

  // Browser storage
  'localStorage',
  'sessionStorage',

  // Location and history
  'location',
  'history',

  // Alert and other UI functions
  'alert',
  'confirm',
  'prompt',

  // Animation and timing
  'requestAnimationFrame',
  'cancelAnimationFrame',
]);

// Libraries that should not be imported in workers
const UNSAFE_IMPORTS = new Set([
  'react',
  'react-dom',
  '@apollo/client',
  'react-router',
  'react-router-dom',
]);

interface UnsafeApiUsage {
  file: string;
  line: number;
  column: number;
  api: string;
  workerFile: string;
  message: string;
  dependencyPath: string[];
  type: 'api' | 'import';
}

class WorkerSafetyChecker {
  private program: ts.Program;
  private checker: ts.TypeChecker;
  private processedFiles = new Set<string>();
  private unsafeUsages: UnsafeApiUsage[] = [];
  private seenErrors = new Set<string>();
  private dependencyPaths = new Map<string, string[]>();

  constructor(private projectRoot: string) {
    // Create TypeScript program
    const configPath = ts.findConfigFile(projectRoot, ts.sys.fileExists, 'tsconfig.json');
    if (!configPath) {
      throw new Error('Could not find tsconfig.json');
    }

    const configFile = ts.readConfigFile(configPath, ts.sys.readFile);
    const parsedConfig = ts.parseJsonConfigFileContent(
      configFile.config,
      ts.sys,
      path.dirname(configPath),
    );

    this.program = ts.createProgram(parsedConfig.fileNames, parsedConfig.options);
    this.checker = this.program.getTypeChecker();
  }

  async checkWorkerSafety(): Promise<UnsafeApiUsage[]> {
    // Find all worker files
    const workerFiles = await this.findWorkerFiles();

    console.log(`Found ${workerFiles.length} worker files:`);
    workerFiles.forEach((file) => console.log(`  - ${file}`));

    // Check each worker file and its dependencies
    for (const workerFile of workerFiles) {
      await this.checkWorkerAndDependencies(workerFile);
    }

    return this.unsafeUsages;
  }

  private async findWorkerFiles(): Promise<string[]> {
    const patterns = ['**/*.worker.ts'];

    const files: string[] = [];
    for (const pattern of patterns) {
      const matches = await glob(pattern, {
        cwd: this.projectRoot,
        absolute: true,
        ignore: ['**/node_modules/**', '**/dist/**', '**/build/**'],
      });
      files.push(...matches);
    }

    // Filter out worker files in mocks directories and remove duplicates
    return [...new Set(files.filter((file) => !file.includes('/mocks/')))];
  }

  private async checkWorkerAndDependencies(workerFile: string): Promise<void> {
    console.log(`\nAnalyzing worker: ${path.relative(this.projectRoot, workerFile)}`);

    // Reset processed files for each worker to ensure we get all transitive deps
    const pathBuildingVisited = new Set<string>();
    const dependencyVisited = new Set<string>();

    // Clear dependency paths for this worker
    this.dependencyPaths.clear();

    // Build dependency paths for this worker
    this.buildDependencyPaths(workerFile, [workerFile], pathBuildingVisited);

    // Get all dependencies of this worker file (now truly recursive)
    const dependencies = this.getDependencies(workerFile, dependencyVisited);
    console.log(`  Found ${dependencies.length} transitive dependencies`);

    // Check the worker file itself
    this.checkFileForUnsafeApis(workerFile, workerFile);

    // Check all dependencies
    for (const dep of dependencies) {
      if (this.isLocalFile(dep)) {
        this.checkFileForUnsafeApis(dep, workerFile);
        this.processedFiles.add(dep);
      }
    }
  }

  private getDependencies(filePath: string, visited = new Set<string>()): string[] {
    const dependencies: string[] = [];

    const collectDependencies = (file: string) => {
      if (visited.has(file)) {
        return;
      }
      visited.add(file);

      const sourceFile = this.program.getSourceFile(file);
      if (!sourceFile) {
        return;
      }

      ts.forEachChild(sourceFile, (node) => {
        if (
          ts.isImportDeclaration(node) &&
          node.moduleSpecifier &&
          ts.isStringLiteral(node.moduleSpecifier)
        ) {
          const moduleName = node.moduleSpecifier.text;

          // Check for unsafe library imports
          if (UNSAFE_IMPORTS.has(moduleName) || moduleName.startsWith('react/')) {
            this.addUnsafeImport(sourceFile, node, moduleName, file, file);
          }

          const resolvedPath = this.resolveImportPath(moduleName, file);

          if (resolvedPath && this.isLocalFile(resolvedPath)) {
            dependencies.push(resolvedPath);
            collectDependencies(resolvedPath); // Recursively collect transitive dependencies
          }
        }
      });
    };

    collectDependencies(filePath);
    return dependencies;
  }

  private buildDependencyPaths(
    filePath: string,
    currentPath: string[],
    visited = new Set<string>(),
  ): void {
    if (visited.has(filePath)) {
      return;
    }
    visited.add(filePath);

    // Store the path to this file
    this.dependencyPaths.set(filePath, [...currentPath]);

    const sourceFile = this.program.getSourceFile(filePath);
    if (!sourceFile) {
      return;
    }

    ts.forEachChild(sourceFile, (node) => {
      if (
        ts.isImportDeclaration(node) &&
        node.moduleSpecifier &&
        ts.isStringLiteral(node.moduleSpecifier)
      ) {
        const moduleName = node.moduleSpecifier.text;
        const resolvedPath = this.resolveImportPath(moduleName, filePath);

        if (resolvedPath && this.isLocalFile(resolvedPath)) {
          // Recursively build paths for dependencies
          this.buildDependencyPaths(resolvedPath, [...currentPath, resolvedPath], visited);
        }
      }
    });
  }

  private resolveImportPath(moduleName: string, fromFile: string): string | null {
    try {
      // Use TypeScript's module resolution
      const resolved = ts.resolveModuleName(
        moduleName,
        fromFile,
        this.program.getCompilerOptions(),
        ts.sys,
      );

      if (resolved.resolvedModule && resolved.resolvedModule.resolvedFileName) {
        return resolved.resolvedModule.resolvedFileName;
      }

      return null;
    } catch (error) {
      console.error(
        `Error resolving import path for module "${moduleName}" from "${fromFile}":`,
        error,
      );
      return null;
    }
  }

  private isLocalFile(filePath: string): boolean {
    return (
      !filePath.includes('node_modules') &&
      (filePath.endsWith('.ts') ||
        filePath.endsWith('.tsx') ||
        filePath.endsWith('.js') ||
        filePath.endsWith('.jsx'))
    );
  }

  private checkFileForUnsafeApis(filePath: string, workerFile: string): void {
    const sourceFile = this.program.getSourceFile(filePath);
    if (!sourceFile) {
      return;
    }

    const relativeWorker = path.relative(this.projectRoot, workerFile);

    const visitNode = (node: ts.Node) => {
      // Check for unsafe library imports
      if (
        ts.isImportDeclaration(node) &&
        node.moduleSpecifier &&
        ts.isStringLiteral(node.moduleSpecifier)
      ) {
        const moduleName = node.moduleSpecifier.text;
        if (UNSAFE_IMPORTS.has(moduleName) || moduleName.startsWith('react/')) {
          this.addUnsafeImport(sourceFile, node, moduleName, filePath, relativeWorker);
        }
      }

      // Check for unsafe global identifiers - only flag direct references
      if (ts.isIdentifier(node)) {
        const text = node.getText(sourceFile);
        if (UNSAFE_BROWSER_APIS.has(text) && !this.isInSafetyCheck(node, text)) {
          // Only flag if this is a direct reference to a global variable
          if (this.isDirectGlobalReference(node)) {
            this.addUnsafeUsage(sourceFile, node, text, filePath, relativeWorker);
          }
        }
      }

      ts.forEachChild(node, visitNode);
    };

    visitNode(sourceFile);
  }

  private isDirectGlobalReference(node: ts.Node): boolean {
    // Only flag identifiers that are direct global references
    // This means they are not:
    // 1. Property names in member access (e.g., 'location' in 'obj.location')
    // 2. Object literals or type annotations
    // 3. Variable declarations or function parameters
    // 4. TypeScript type definitions and interface properties

    if (!ts.isIdentifier(node)) {
      return false;
    }

    const parent = node.parent;
    if (!parent) {
      return true; // Top-level identifier
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

    // Not a direct reference if it's a method signature
    if (ts.isMethodSignature(parent) && parent.name === node) {
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
      // Check if this property access is in a type context
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

    // Not a direct reference if it's a function declaration name
    if (ts.isFunctionDeclaration(parent) && parent.name === node) {
      return false;
    }

    // Not a direct reference if it's in a binding pattern (destructuring)
    if (ts.isBindingElement(parent) && (parent.name === node || parent.propertyName === node)) {
      return false;
    }

    // Not a direct reference if it's the left side of a type annotation (:)
    if (
      ts.isPropertySignature(parent) ||
      ts.isMethodDeclaration(parent) ||
      ts.isGetAccessorDeclaration(parent) ||
      ts.isSetAccessorDeclaration(parent)
    ) {
      return false;
    }

    // Check if this identifier is shadowed by a local declaration
    if (this.isIdentifierShadowed(node)) {
      return false;
    }

    // This covers most cases where we want to flag actual usage
    return true;
  }

  private isIdentifierShadowed(node: ts.Identifier): boolean {
    // Walk up the scope chain to see if this identifier is declared locally
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
            return true; // Found a parameter with the same name
          }
        }
      }

      // Check for variable declarations in this scope
      if (ts.isBlock(current) || ts.isSourceFile(current) || ts.isModuleBlock(current)) {
        const statements = current.statements;
        for (const statement of statements) {
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

  private isInSafetyCheck(node: ts.Node, apiName: string): boolean {
    // Look for patterns like: typeof window !== 'undefined'
    let parent = node.parent;
    let depth = 0;
    const maxDepth = 10;

    while (parent && depth < maxDepth) {
      if (ts.isIfStatement(parent)) {
        const condition = parent.expression;

        // Check for typeof checks
        if (ts.isBinaryExpression(condition)) {
          const {left, operatorToken, right} = condition;

          if (
            (operatorToken.kind === ts.SyntaxKind.ExclamationEqualsEqualsToken ||
              operatorToken.kind === ts.SyntaxKind.ExclamationEqualsToken) &&
            ts.isTypeOfExpression(left) &&
            ts.isStringLiteral(right) &&
            right.text === 'undefined'
          ) {
            // Check if the typeof is checking the same variable as the unsafe usage
            if (ts.isIdentifier(left.expression)) {
              const checkedVariable = left.expression.getText();
              return checkedVariable === apiName;
            }
          }
        }

        // Check for logical AND patterns like: window && window.something
        if (
          ts.isBinaryExpression(condition) &&
          condition.operatorToken.kind === ts.SyntaxKind.AmpersandAmpersandToken
        ) {
          // For now, return true for any && pattern - could be made more specific
          return true;
        }
      }

      parent = parent.parent;
      depth++;
    }

    return false;
  }

  private addUnsafeUsage(
    sourceFile: ts.SourceFile,
    node: ts.Node,
    api: string,
    file: string,
    workerFile: string,
  ): void {
    const {line, character} = sourceFile.getLineAndCharacterOfPosition(node.getStart());

    // Convert file to relative for display but use absolute for dependency lookup
    const relativeFile = path.relative(this.projectRoot, file);

    // Create a unique identifier for this error (file:line:column:api:worker)
    const errorKey = `${relativeFile}:${line + 1}:${character + 1}:${api}:${workerFile}`;

    // Skip if we've already seen this exact error
    if (this.seenErrors.has(errorKey)) {
      return;
    }
    this.seenErrors.add(errorKey);

    let message = `${api} is not available in worker context`;
    if (api.includes('Animation')) {
      message += ' (use setTimeout/setInterval instead)';
    } else if (api.includes('navigator')) {
      message += ' (use userAgent from worker context if needed)';
    } else if (api.includes('location')) {
      message += ' (use self.location in worker if needed)';
    }

    // Use absolute file path for dependency lookup
    const storedPath = this.dependencyPaths.get(file) || [file];

    this.unsafeUsages.push({
      file: relativeFile, // Store relative path for display
      line: line + 1,
      column: character + 1,
      api,
      workerFile,
      message,
      dependencyPath: storedPath,
      type: 'api',
    });
  }

  private addUnsafeImport(
    sourceFile: ts.SourceFile,
    node: ts.Node,
    importName: string,
    file: string,
    workerFile: string,
  ): void {
    const {line, character} = sourceFile.getLineAndCharacterOfPosition(node.getStart());

    // Convert file to relative for display but use absolute for dependency lookup
    const relativeFile = path.relative(this.projectRoot, file);

    // Create a unique identifier for this error
    const errorKey = `${relativeFile}:${line + 1}:${character + 1}:import:${importName}:${workerFile}`;

    // Skip if we've already seen this exact error
    if (this.seenErrors.has(errorKey)) {
      return;
    }
    this.seenErrors.add(errorKey);

    let message = `${importName} should not be imported in worker context`;
    if (importName === 'react' || importName.startsWith('react/')) {
      message += ' (increases bundle size and not needed in workers)';
    } else if (importName === '@apollo/client') {
      message += ' (GraphQL client not needed in workers)';
    }

    // Use absolute file path for dependency lookup
    const storedPath = this.dependencyPaths.get(file) || [file];

    this.unsafeUsages.push({
      file: relativeFile,
      line: line + 1,
      column: character + 1,
      api: `import ${importName}`,
      workerFile,
      message,
      dependencyPath: storedPath,
      type: 'import',
    });
  }
}

async function main() {
  const projectRoot = process.cwd();
  console.log(`Checking worker safety in: ${projectRoot}`);

  try {
    const checker = new WorkerSafetyChecker(projectRoot);
    const unsafeUsages = await checker.checkWorkerSafety();

    if (unsafeUsages.length === 0) {
      console.log('\n✅ All worker files and their dependencies are safe!');
      process.exit(0);
    }

    console.log(`\n❌ Found ${unsafeUsages.length} unsafe browser API usage(s):\n`);

    // Group usages by file at the top level
    const byFile = new Map<string, UnsafeApiUsage[]>();
    for (const usage of unsafeUsages) {
      if (!byFile.has(usage.file)) {
        byFile.set(usage.file, []);
      }
      const fileUsages = byFile.get(usage.file);
      if (fileUsages) {
        fileUsages.push(usage);
      }
    }

    for (const [file, fileUsages] of byFile.entries()) {
      console.log(`\n📄 ${file}:`);

      // Get unique workers that use this file
      const affectedWorkers = [...new Set(fileUsages.map((usage) => usage.workerFile))];
      console.log(`   🔗 Affects workers: ${affectedWorkers.join(', ')}`);

      // Show all unique errors in this file (deduplicate by line:column:api)
      const uniqueErrors = new Map<string, UnsafeApiUsage>();
      for (const usage of fileUsages) {
        const errorKey = `${usage.line}:${usage.column}:${usage.api}`;
        if (!uniqueErrors.has(errorKey)) {
          uniqueErrors.set(errorKey, usage);
        }
      }

      for (const usage of uniqueErrors.values()) {
        console.log(`   ❌ ${usage.file}:${usage.line}:${usage.column} - ${usage.api}`);
        console.log(`      ${usage.message}`);
      }

      // Show dependency path after all violations for this file
      const firstUsage = fileUsages[0];
      if (firstUsage.dependencyPath.length > 1) {
        const pathStr = firstUsage.dependencyPath
          .map((p) => path.relative(process.cwd(), p))
          .join(' → ');
        console.log(`   📍 Example dependency path: ${pathStr}`);
      } else {
        console.log(`   📍 Used directly by worker(s)`);
      }
    }

    process.exit(1);
  } catch (error) {
    console.error('Error checking worker safety:', error);
    process.exit(1);
  }
}

if (require.main === module) {
  main().catch(console.error);
}
