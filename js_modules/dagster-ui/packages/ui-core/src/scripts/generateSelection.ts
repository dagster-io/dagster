import {execFileSync} from 'child_process';
import path from 'path';

const SELECTION_GRAMMAR_FILE_PATH = path.resolve('./src/selection/SelectionAutoComplete.g4');
execFileSync('antlr4ng', [
  '-Dlanguage=TypeScript',
  '-visitor',
  '-o',
  './src/selection/generated',
  SELECTION_GRAMMAR_FILE_PATH,
]);

const files = [
  'SelectionAutoCompleteLexer.ts',
  'SelectionAutoCompleteListener.ts',
  'SelectionAutoCompleteParser.ts',
  'SelectionAutoCompleteVisitor.ts',
];

files.forEach((file) => {
  execFileSync('yarn', ['prettier', `./src/selection/generated/${file}`, '--write']);
});
