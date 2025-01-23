const fs = require('fs');
const path = require('path');

const DOCUMENTATION_DIRECTORY = 'docs';
const VALID_DOCUMENT_EXTENSIONS = ['.md', '.mdx'];
const CODE_EXAMPLE_PATH_REGEX = /<CodeExample\s+[^>]*path=["']([^"']+)["'][^>]*>/g;

/**
 * Returns a list of file paths for a given `dir`.
 */
function getAllDocuments(dir) {
  let results = [];
  const list = fs.readdirSync(dir);

  list.forEach((file) => {
    file = path.join(dir, file);
    const stat = fs.statSync(file);
    if (stat && stat.isDirectory()) {
      results = results.concat(getAllDocuments(file)); // Recurse into subdirectory
    } else {
      if (VALID_DOCUMENT_EXTENSIONS.indexOf(path.extname(file)) !== -1) {
        results.push(file); // Add file to results
      }
    }
  });

  return results;
}

/**
 * Extracts all `regex` group `1` matches found in a list of `files`.
 */
function getUniqueRegexMatches(files, regex) {
  const matches = new Set();

  files.forEach((file) => {
    const content = fs.readFileSync(file, 'utf-8');
    let foundMatches;
    while ((foundMatches = regex.exec(content)) !== null) {
      matches.add(foundMatches[1]); // Extract group 1
    }
  });

  return Array.from(matches);
}

const files = getAllDocuments('docs');

const uniqueMatches = getUniqueRegexMatches(files, CODE_EXAMPLE_PATH_REGEX);

const lines = [
  'export const CODE_EXAMPLE_PATH_MAPPINGS = {',
  ...uniqueMatches.map((path) => `  '${path}': '!!raw-loader!/../../examples/${path}',`),
  '};',
].join('\n');


fs.writeFile('src/code-examples-content.js', lines, (err) => {
  if (err) throw err;
  console.log('The data was appended!');
});
