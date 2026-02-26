// findCircularDeps.ts
import path from 'path';

import {Project} from 'ts-morph';

const project = new Project({
  tsConfigFilePath: 'tsconfig.json',
});

const graph = new Map<string, Set<string>>();

for (const sourceFile of project.getSourceFiles()) {
  const filePath = sourceFile.getFilePath();
  const imports = sourceFile
    .getImportDeclarations()
    .filter((decl) => !decl.isTypeOnly())
    .map((decl) =>
      path.resolve(sourceFile.getDirectoryPath(), decl.getModuleSpecifierValue() + '.ts'),
    );
  graph.set(filePath, new Set(imports.filter((f) => project.getSourceFile(f))));
}

const visited = new Set<string>();
const stack = new Set<string>();

function dfs(node: string, pathStack: string[]) {
  if (stack.has(node)) {
    const cycleStart = pathStack.indexOf(node);
    const cycle = pathStack.slice(cycleStart).concat(node);
    const isGenerated = cycle.every((p) => p.includes('/generated/'));
    if (!isGenerated) {
      console.log('\nCircular dependency detected:');
      console.log(cycle.join(' -> '));
    }
    return;
  }

  if (visited.has(node)) {
    return;
  }

  visited.add(node);
  stack.add(node);
  pathStack.push(node);

  for (const neighbor of graph.get(node) || []) {
    dfs(neighbor, pathStack);
  }

  stack.delete(node);
  pathStack.pop();
}

for (const node of graph.keys()) {
  dfs(node, []);
}
