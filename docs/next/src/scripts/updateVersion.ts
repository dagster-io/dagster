import fs from 'fs';
import path from 'path';

const TARGET_FILE_PATH = path.resolve(
  __dirname,
  '..',
  'pages/versions/index.mdx',
);

// equivalent of `if __name__ == '__main__'`
if (require.main === module) {
  main();
}

function main() {
  if (process.argv.length !== 3) {
    throw new Error('❌ Usage: yarn update-version <new version>');
  }

  const newVersion = process.argv[2];
  const currentContent = fs.readFileSync(TARGET_FILE_PATH, 'utf-8');

  const { oldVersion, newContent } = updateVersion(currentContent, newVersion);
  console.log(
    `Updating the current version from ${oldVersion} to ${newVersion}...\n`,
  );

  fs.writeFileSync(TARGET_FILE_PATH, newContent, 'utf-8');
  console.log(`✅ Successfully updated ${TARGET_FILE_PATH}.\n`);
}

export function updateVersion(
  fileContent: string,
  newVersion: string,
): {
  oldVersion: string;
  newContent: string;
} {
  const lines = fileContent.split('\n');

  // find old version
  const versionRegex = /\| +\*\*(\d+\.\d+\.\d+)\*\* +\|/;
  const oldVersion = lines
    .map((line) => line.match(versionRegex)?.[1])
    .find(Boolean);

  if (!oldVersion) {
    throw new Error('❌ Invalid input content');
  }

  // find lines with old version
  let oldVersionLines: { index: number; line: string }[] = [];
  for (let index = 0; index < lines.length; index++) {
    const line = lines[index];
    if (line.includes(oldVersion)) {
      oldVersionLines.push({ index, line });
    }
  }

  // update versions
  const { index: oldVersionIndex, line: oldVersionLine } = oldVersionLines[1];
  oldVersionLines.map(({ index }) => {
    lines[index] = lines[index].replace(
      new RegExp(oldVersion, 'g'),
      newVersion,
    );
  });
  lines.splice(oldVersionIndex + 2, 0, oldVersionLine);

  return {
    oldVersion: oldVersion,
    newContent: lines.join('\n'),
  };
}
