import {execSync} from 'child_process';
import path from 'path';

const PARTITION_SELECTION_GRAMMAR_FILE_PATH = path.resolve(
  './src/partitions/PartitionSelection.g4',
);
execSync(
  `antlr4ts -visitor -o ./src/partitions/generated ${PARTITION_SELECTION_GRAMMAR_FILE_PATH}`,
);

const files = [
  'PartitionSelectionLexer.ts',
  'PartitionSelectionListener.ts',
  'PartitionSelectionParser.ts',
  'PartitionSelectionVisitor.ts',
];

files.forEach((file) => {
  execSync(`yarn prettier ./src/partitions/generated/${file} --write`);
});
