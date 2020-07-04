import fs from 'fs';
import path from 'path';

export interface Versions {
  currentVersion: Version;
  allVersions: Version[];
}
export interface Version {
  version: string;
  documentation: string;
  releaseNotes: string;
  note?: string;
}

const JSON_FILE_PATH = path.resolve(__dirname, '..', 'versions.json');
const MDX_FILE_PATH = path.resolve(__dirname, '..', 'pages/versions/index.mdx');

const JSON_CONTENT = {
  currentVersion: {
    version: '<version>',
    documentation: '/install',
    releaseNotes:
      'https://github.com/dagster-io/dagster/releases/tag/<version>',
  },
  allVersion: {
    version: '<version>',
    documentation: '/<version>/install',
    releaseNotes:
      'https://github.com/dagster-io/dagster/releases/tag/<version>',
  },
};

const currVersionRow = (
  version: string,
  documentation: string,
  releaseNotes: string,
) =>
  `| **${version}** | [Documentation](${documentation}) | [Release Notes](${releaseNotes}) |`;

const allVersionRow = (
  version: string,
  documentation: string,
  releaseNotes: string,
  note: string = ' ',
) =>
  `| **${version}** | [Documentation](${documentation}) | [Release Notes](${releaseNotes}) | ${note} |`;

export function updateVersionsJson(
  jsonString: string,
  newVersion: string,
): {
  oldVersion: string;
  newJsonContent: string;
} {
  const jsonContent: Versions = JSON.parse(jsonString);
  const oldVersion = jsonContent.currentVersion.version;

  if (oldVersion === newVersion) {
    return {
      oldVersion,
      newJsonContent: jsonString,
    };
  }

  jsonContent.currentVersion = JSON.parse(
    JSON.stringify(JSON_CONTENT.currentVersion).replace(
      /<version>/g,
      newVersion,
    ),
  );
  jsonContent.allVersions.unshift(
    JSON.parse(
      JSON.stringify(JSON_CONTENT.allVersion).replace(/<version>/g, newVersion),
    ),
  );
  return {
    oldVersion,
    newJsonContent: JSON.stringify(jsonContent, null, 4),
  };
}

export function generateVersionsMDX(
  jsonString: string,
): {
  mdxContent: string;
} {
  const jsonContent: Versions = JSON.parse(jsonString);
  return {
    mdxContent: [
      '# Dagster Versions',
      '',
      '## Current version (Stable)',
      '',
      currVersionRow(
        jsonContent.currentVersion.version,
        jsonContent.currentVersion.documentation,
        jsonContent.currentVersion.releaseNotes,
      ),
      '| ---- | ---- | ---- |',
      '',
      '',
      '## All Versions',
      '',
      ...jsonContent.allVersions
        .slice(0, 1)
        .map((obj) =>
          allVersionRow(
            obj.version,
            obj.documentation,
            obj.releaseNotes,
            obj.note,
          ),
        ),
      '| ---- | ---- | ---- | ---- |',
      ...jsonContent.allVersions
        .slice(1)
        .map((obj) =>
          allVersionRow(
            obj.version,
            obj.documentation,
            obj.releaseNotes,
            obj.note,
          ),
        ),
    ].join('\n'),
  };
}

// equivalent of `if __name__ == '__main__'`
if (require.main === module) {
  main();
}

function main() {
  if (process.argv.length !== 3) {
    throw new Error('❌ Usage: yarn update-version <new version>');
  }

  const newVersion = process.argv[2];
  const currentJsonContent = fs.readFileSync(JSON_FILE_PATH, 'utf-8');

  const { oldVersion, newJsonContent } = updateVersionsJson(
    currentJsonContent,
    newVersion,
  );
  const { mdxContent } = generateVersionsMDX(newJsonContent);

  console.log(
    `Updating the current version from ${oldVersion} to ${newVersion}...\n`,
  );
  // write to versions.json
  fs.writeFileSync(JSON_FILE_PATH, newJsonContent, 'utf-8');
  console.log(`✅ Successfully updated ${JSON_FILE_PATH}.\n`);

  // write to versions/index.mdx
  fs.writeFileSync(MDX_FILE_PATH, mdxContent, 'utf-8');
  console.log(`✅ Successfully updated ${MDX_FILE_PATH}.\n`);
}
