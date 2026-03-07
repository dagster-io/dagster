const fs = require('fs');
const path = require('path');

function findRelativeImportPath(currentFilePath, targetPath) {
  let currentDir = path.dirname(currentFilePath);

  while (currentDir !== path.parse(currentDir).root) {
    if (currentDir === '.') {
      break;
    }
    const targetFilePath = path.join(currentDir, targetPath);

    if (fs.existsSync(targetFilePath)) {
      return path.relative(path.dirname(currentFilePath), path.dirname(targetFilePath));
    }

    currentDir = path.dirname(currentDir);
  }

  return null;
}

module.exports = {findRelativeImportPath};
