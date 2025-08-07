import * as path from 'path';

import {glob} from 'glob';
import * as ts from 'typescript';

import {findUnsafeApiUsages, generateErrorMessage} from './ast-analyzer';
import {UnsafeApiUsage} from './types';

export class WorkerSafetyChecker {
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

  async findWorkerFiles(): Promise<string[]> {
    const patterns = ['**/*.worker.ts'];
    const files: string[] = [];

    for (const pattern of patterns) {
      const found = await glob(pattern, {
        cwd: this.projectRoot,
        absolute: true,
        ignore: ['**/node_modules/**'],
      });
      files.push(...found);
    }

    // Filter out mock files
    return files.filter((file) => !file.includes('/mocks/'));
  }

  private async checkWorkerAndDependencies(workerFile: string): Promise<void> {
    console.log(`\nChecking worker: ${path.relative(this.projectRoot, workerFile)}`);

    // Reset dependency paths for this worker
    this.dependencyPaths.clear();

    // Build full dependency paths for this worker
    this.buildDependencyPaths(workerFile, [workerFile], new Set());

    // Get all dependencies of this worker (transitive)
    const dependencies = this.getDependencies(workerFile, new Set());
    console.log(`  Found ${dependencies.size} transitive dependencies`);

    // Check the worker file itself and all its dependencies
    const filesToCheck = [workerFile, ...Array.from(dependencies)];
    for (const file of filesToCheck) {
      this.checkFileForUnsafeApis(file, workerFile);
    }
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

    // Get direct dependencies and build paths to them
    const directDeps = this.getDirectDependencies(filePath);
    for (const dep of directDeps) {
      this.buildDependencyPaths(dep, [...currentPath, dep], visited);
    }
  }

  private getDependencies(filePath: string, visited = new Set<string>()): Set<string> {
    if (visited.has(filePath)) {
      return new Set();
    }
    visited.add(filePath);

    const dependencies = new Set<string>();
    const directDeps = this.getDirectDependencies(filePath);

    for (const dep of directDeps) {
      dependencies.add(dep);
      // Recursively get dependencies of dependencies
      const nestedDeps = this.getDependencies(dep, visited);
      nestedDeps.forEach((nestedDep) => dependencies.add(nestedDep));
    }

    return dependencies;
  }

  private getDirectDependencies(filePath: string): string[] {
    const sourceFile = this.program.getSourceFile(filePath);
    if (!sourceFile) {
      return [];
    }

    const dependencies: string[] = [];

    ts.forEachChild(sourceFile, (node) => {
      if (ts.isImportDeclaration(node) && node.moduleSpecifier) {
        if (ts.isStringLiteral(node.moduleSpecifier)) {
          const moduleName = node.moduleSpecifier.text;
          const resolvedPath = this.resolveImportPath(moduleName, filePath);
          if (resolvedPath) {
            dependencies.push(resolvedPath);
          }
        }
      }
    });

    return dependencies;
  }

  private resolveImportPath(moduleName: string, fromFile: string): string | null {
    try {
      const result = ts.resolveModuleName(
        moduleName,
        fromFile,
        this.program.getCompilerOptions(),
        ts.sys,
      );

      if (result.resolvedModule) {
        return result.resolvedModule.resolvedFileName;
      }
    } catch (error) {
      console.error(`Error resolving module ${moduleName} from ${fromFile}:`, error);
    }

    return null;
  }

  private checkFileForUnsafeApis(file: string, workerFile: string): void {
    if (this.processedFiles.has(`${file}:${workerFile}`)) {
      return;
    }
    this.processedFiles.add(`${file}:${workerFile}`);

    const sourceFile = this.program.getSourceFile(file);
    if (!sourceFile) {
      return;
    }

    // Use the extracted analysis function
    const usages = findUnsafeApiUsages(sourceFile, file);

    for (const usage of usages) {
      const relativeFile = path.relative(this.projectRoot, file);
      const relativeWorkerFile = path.relative(this.projectRoot, workerFile);

      const message = generateErrorMessage(usage.api, usage.type);

      this.addUnsafeUsage(
        sourceFile,
        usage.node,
        usage.api,
        relativeFile,
        relativeWorkerFile,
        message,
        usage.type,
      );
    }
  }

  private addUnsafeUsage(
    sourceFile: ts.SourceFile,
    node: ts.Node,
    api: string,
    file: string,
    workerFile: string,
    message: string,
    type: 'api' | 'import',
  ): void {
    const {line, character} = sourceFile.getLineAndCharacterOfPosition(node.getStart());

    // Create a unique key to avoid duplicate errors
    const errorKey = `${file}:${line + 1}:${character + 1}:${api}:${workerFile}`;
    if (this.seenErrors.has(errorKey)) {
      return;
    }
    this.seenErrors.add(errorKey);

    // Use absolute file path for dependency lookup
    const absoluteFile = path.resolve(this.projectRoot, file);
    const storedPath = this.dependencyPaths.get(absoluteFile) || [absoluteFile];

    this.unsafeUsages.push({
      file,
      line: line + 1,
      column: character + 1,
      api,
      workerFile,
      message,
      dependencyPath: storedPath,
      type,
    });
  }

  // Expose internal methods for testing
  getDirectDependenciesForTesting(filePath: string): string[] {
    return this.getDirectDependencies(filePath);
  }

  getDependenciesForTesting(filePath: string): Set<string> {
    return this.getDependencies(filePath, new Set());
  }

  checkFileForTesting(file: string, workerFile: string): void {
    this.checkFileForUnsafeApis(file, workerFile);
  }

  getUnsafeUsages(): UnsafeApiUsage[] {
    return this.unsafeUsages;
  }

  reset(): void {
    this.processedFiles.clear();
    this.unsafeUsages = [];
    this.seenErrors.clear();
    this.dependencyPaths.clear();
  }
}
