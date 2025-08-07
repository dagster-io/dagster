#!/usr/bin/env tsx

import * as path from 'path';

import {WorkerSafetyChecker} from './worker-safety/checker';

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
    const byFile = new Map();
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
      const affectedWorkers = [...new Set(fileUsages.map((usage: any) => usage.workerFile))];
      console.log(`   🔗 Affects workers: ${affectedWorkers.join(', ')}`);

      // Show all unique errors in this file (deduplicate by line:column:api)
      const uniqueErrors = new Map();
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
          .map((p: string) => path.relative(process.cwd(), p))
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
