import {execFileSync} from 'child_process';
import path from 'path';

const RUN_SELECTION_GRAMMAR_FILE_PATH = path.resolve('./src/run-selection/RunSelection.g4');
execFileSync('antlr4ng', [
  '-Dlanguage=TypeScript',
  '-visitor',
  '-o',
  './src/run-selection/generated',
  RUN_SELECTION_GRAMMAR_FILE_PATH,
]);

const files = [
  'RunSelectionLexer.ts',
  'RunSelectionListener.ts',
  'RunSelectionParser.ts',
  'RunSelectionVisitor.ts',
];

files.forEach((file) => {
  execFileSync('yarn', ['prettier', `./src/run-selection/generated/${file}`, '--write']);
});
