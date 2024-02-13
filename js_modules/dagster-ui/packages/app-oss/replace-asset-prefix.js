/* eslint-disable @typescript-eslint/no-var-requires */
const fs = require('fs');
const path = require('path');

function replaceStringInFile(filePath, searchString, replacement) {
  const fileContent = fs.readFileSync(filePath, 'utf8');
  const replacedContent = fileContent.replace(new RegExp(searchString, 'g'), replacement);
  fs.writeFileSync(filePath, replacedContent);
}

function processDirectory(directory) {
  const files = fs.readdirSync(directory);

  for (const file of files) {
    const filePath = path.join(directory, file);

    const isDirectory = fs.statSync(filePath).isDirectory();

    if (isDirectory) {
      // Recursively process subdirectories
      processDirectory(filePath);
    } else if (file.endsWith('.js')) {
      replaceStringInFile(
        filePath,
        '"BUILDTIME_ASSETPREFIX_REPLACE_ME',
        // if typeof window === "undefined" then we are inside a web worker
        // Grab the path from the location object
        '(() => {if (typeof window === "undefined") {return self.location.pathname.split("/_next/")[0]} return self.__webpack_public_path__ || "";})() + "',
      );
    }
  }
}

processDirectory(__dirname + '/build/');
