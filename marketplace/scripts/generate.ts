import fs from 'fs';
import path from 'path';

import {ESLint} from 'eslint';
import {read} from 'to-vfile';
import {matter} from 'vfile-matter';

import {IntegrationFrontmatter} from './types';

const PATH_TO_INTEGRATION_DOCS = path.resolve('../docs/docs/integrations/libraries');
const PATH_TO_INTEGRATION_LOGOS = path.resolve('../docs/static');
const PATH_TO_EXAMPLES = path.resolve('../examples');
const OUTPUT_TARGET_DIR = path.resolve('./__generated__');
const OUTPUT_TARGET_LOGOS_DIR = path.join(OUTPUT_TARGET_DIR, 'logos');

const CODE_EXAMPLE_PATH_REGEX =
  /<(?:(?:CodeExample)|(?:CliInvocationExample))\s+[^>]*path=["']([^"']+)["'][^>]*language=["']([^"']+)["'][^>]*>/g;

function camelize(str: string) {
  return str.replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
}

const eslint = new ESLint({fix: true});

/**
 * This script copies integration documentation and logos from the `docs` project for reuse
 * in the Integration Marketplace in the Dagster app.
 *
 * Integration markdown files are flattened out from the `docs` file structure, and frontmatter is
 * extracted for use in routing and UI.
 */
async function main() {
  // Reset target directories before generating new files.
  await fs.promises.rm(OUTPUT_TARGET_DIR, {recursive: true, force: true});
  await fs.promises.mkdir(OUTPUT_TARGET_DIR, {recursive: true});
  await fs.promises.mkdir(OUTPUT_TARGET_LOGOS_DIR, {recursive: true});

  const INTEGRATION_DOCS_FILES = await fs.promises.readdir(PATH_TO_INTEGRATION_DOCS, {
    recursive: true,
  });

  const mdFiles = INTEGRATION_DOCS_FILES.filter((file) => file.endsWith('.md'));
  const fullList: string[] = [];
  const frontmatterList: IntegrationFrontmatter[] = [];

  console.log(`🔍 Found ${mdFiles.length} .md files. Only integration files will be processed.`);

  for (const fileName of mdFiles) {
    const filePath = path.resolve(PATH_TO_INTEGRATION_DOCS, fileName);
    const file = await read(filePath);

    // Extract frontmatter, leave only markdown behind.
    matter(file, {strip: true});

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const matterResult = file.data.matter as any;

    // Skip any md files that are not for integrations (e.g. index files for categories).
    if (matterResult.layout !== 'Integration') {
      continue;
    }

    let camelizedFileName = '';

    if (fileName.includes('/')) {
      // Handle files that are within nested directories.
      camelizedFileName = camelize(
        fileName.replace('/index.md', '').replaceAll('/', '-').replace('.md', ''),
      );
    } else {
      camelizedFileName = camelize(fileName.replace('.md', ''));
    }

    fullList.push(camelizedFileName);

    const frontmatter: IntegrationFrontmatter = {
      id: camelizedFileName,
      status: matterResult.status ?? '',
      name: matterResult.name ?? '',
      title: matterResult.title ?? '',
      excerpt: matterResult.excerpt ?? '',
      partnerlink: matterResult.partnerlink ?? '',
      categories: matterResult.categories ?? [],
      enabledBy: matterResult.enabledBy ?? [],
      enables: matterResult.enables ?? [],
      tags: matterResult.tags ?? [],
    };

    frontmatterList.push(frontmatter);

    let logoFileExists = false;
    const logoPath = matterResult.sidebar_custom_props?.logo;

    if (logoPath) {
      try {
        await fs.promises.stat(path.join(PATH_TO_INTEGRATION_LOGOS, logoPath));
        logoFileExists = true;
      } catch {}
    }

    let logoFilename = null;
    if (logoFileExists) {
      logoFilename = logoPath?.split('/').pop()?.toLowerCase();
    }

    const outputPath = path.join(OUTPUT_TARGET_DIR, `${camelizedFileName}.json`);

    let content = String(file).trim();

    const codeExampleMatches: {
      fullMatch: string;
      filePath: string;
      language: string;
    }[] = [];

    let foundMatches: RegExpExecArray | null;
    while ((foundMatches = CODE_EXAMPLE_PATH_REGEX.exec(content)) !== null) {
      const [fullMatch, filePath, language] = foundMatches;
      codeExampleMatches.push({fullMatch, filePath, language});
    }

    for (const {fullMatch, filePath, language} of codeExampleMatches) {
      if (filePath) {
        const codeFromFile = await fs.promises.readFile(
          path.join(PATH_TO_EXAMPLES, filePath),
          'utf8',
        );

        content = content.replace(
          fullMatch,
          `
\`\`\`${language}
${codeFromFile.trim()}
\`\`\`
        `,
        );
      }
    }

    const packagedObject = {
      frontmatter,
      logoFilename,
      content,
    };

    const output = JSON.stringify(packagedObject, null, 2);

    await fs.promises.writeFile(outputPath, output);

    // Copy the logo to the output directory
    if (logoFilename) {
      await fs.promises.copyFile(
        path.join(PATH_TO_INTEGRATION_LOGOS, logoPath),
        path.join(OUTPUT_TARGET_LOGOS_DIR, logoFilename),
      );
    }
  }

  console.log(`✅ Successfully processed ${fullList.length} integrations.`);

  const indexOutput = JSON.stringify(frontmatterList, null, 2);

  await fs.promises.writeFile(path.join(OUTPUT_TARGET_DIR, 'index.json'), indexOutput);

  console.log(`✅ Created index file.`);

  const eslintOutput = await eslint.lintFiles([`${OUTPUT_TARGET_DIR}/**/*.json`]);
  await ESLint.outputFixes(eslintOutput);

  console.log(`✅ Ran eslint.`);

  console.log('✨ Integration docs generated successfully.');
}

main();
