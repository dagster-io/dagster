import {execSync} from 'child_process';
import path from 'path';

const RUN_SELECTION_GRAMMAR_FILE_PATH = path.resolve('./src/run-selection/RunSelection.g4');
execSync(`antlr4ts -visitor -o ./src/run-selection/generated ${RUN_SELECTION_GRAMMAR_FILE_PATH}`);

const files = [
  'RunSelectionLexer.ts',
  'RunSelectionListener.ts',
  'RunSelectionParser.ts',
  'RunSelectionVisitor.ts',
];

files.forEach((file) => {
  execSync(`yarn prettier ./src/run-selection/generated/${file} --write`);
});
