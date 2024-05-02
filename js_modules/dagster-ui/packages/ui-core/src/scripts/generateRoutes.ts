import {execSync} from 'child_process';
import fs from 'fs';
import path from 'path';

import ts from 'typescript';

const routeFilesFolder = 'src'; // The folder where your TypeScript files are located

/**
 * Recursively deletes all files ending in `.routes.ts` within the specified directory.
 * @param dirPath The directory path to search within.
 */
function deleteRouteFiles(dirPath: string) {
  const entries = fs.readdirSync(dirPath, {withFileTypes: true});

  entries.forEach((entry) => {
    const fullPath = path.join(dirPath, entry.name);
    if (entry.isDirectory()) {
      // Recursively delete in sub-directories
      deleteRouteFiles(fullPath);
    } else if (entry.isFile() && entry.name.endsWith('.routes.ts')) {
      // Delete files ending with `.routes.ts`
      fs.unlinkSync(fullPath);
    }
  });
}

// Function to find all TypeScript files in a directory recursively
function getAllTsFiles(dirPath: string, arrayOfFiles: string[] = []) {
  const files = fs.readdirSync(dirPath);

  files.forEach((file) => {
    if (fs.statSync(dirPath + '/' + file).isDirectory()) {
      arrayOfFiles = getAllTsFiles(dirPath + '/' + file, arrayOfFiles);
    } else if (
      file.endsWith('.tsx') &&
      !file.endsWith('.test.tsx') &&
      !file.endsWith('.stories.tsx')
    ) {
      arrayOfFiles.push(path.join(dirPath, '/', file));
    }
  });

  return arrayOfFiles;
}

// Function to extract route definitions from a TypeScript file
function extractRoutes(filePath: string): any[] {
  const fileContent = fs.readFileSync(filePath, 'utf8');
  const sourceFile = ts.createSourceFile(filePath, fileContent, ts.ScriptTarget.Latest, true);

  const routes: any[] = [];

  function visit(node: ts.Node) {
    if (ts.isJsxElement(node) || ts.isJsxSelfClosingElement(node)) {
      const openingElement = ts.isJsxElement(node) ? node.openingElement : node;
      if (ts.isJsxOpeningElement(openingElement) || ts.isJsxSelfClosingElement(openingElement)) {
        const tagName = openingElement.tagName;
        if (ts.isIdentifier(tagName) && tagName.escapedText === 'Route') {
          const pathAttribute = openingElement.attributes.properties.find(
            (prop: ts.JsxAttributeLike): prop is ts.JsxAttribute =>
              ts.isJsxAttribute(prop) &&
              ts.isIdentifier(prop.name) &&
              prop.name.escapedText === 'path',
          );
          const exactAttribute = openingElement.attributes.properties.find(
            (prop: ts.JsxAttributeLike): prop is ts.JsxAttribute =>
              ts.isJsxAttribute(prop) &&
              ts.isIdentifier(prop.name) &&
              prop.name.escapedText === 'exact',
          );

          if (
            pathAttribute &&
            pathAttribute.initializer &&
            ts.isStringLiteral(pathAttribute.initializer)
          ) {
            const route: any = {path: pathAttribute.initializer.text};
            if (
              exactAttribute &&
              exactAttribute.initializer &&
              ts.isJsxExpression(exactAttribute.initializer) &&
              exactAttribute.initializer.expression
            ) {
              // Check if the expression is a TrueKeyword
              if (
                exactAttribute &&
                (exactAttribute.initializer === undefined ||
                  exactAttribute.initializer?.expression?.kind === ts.SyntaxKind.TrueKeyword)
              ) {
                route.props = {exact: true};
              }
            }
            routes.push(route);
          }
        }
      }
    }
    ts.forEachChild(node, visit);
  }

  visit(sourceFile);
  return routes;
}

// Main function to process all files and generate routes
function generateRouteFiles() {
  deleteRouteFiles(routeFilesFolder);
  const tsFiles = getAllTsFiles(routeFilesFolder);
  tsFiles.forEach((file) => {
    const routes = extractRoutes(file);
    if (routes.length) {
      const outputFilePath = file.replace('.tsx', '.routes.ts');
      const content = `export const ${path
        .basename(file)
        .replace('.tsx', '')}Routes = ${JSON.stringify(routes, null, 2)};\n`;
      fs.writeFileSync(outputFilePath, content);
      execSync(`yarn prettier --write ./${outputFilePath}`, {stdio: 'inherit'});
    }
  });
}
generateRouteFiles();
