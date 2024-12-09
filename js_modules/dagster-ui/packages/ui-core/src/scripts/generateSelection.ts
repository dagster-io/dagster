import {execSync} from 'child_process';
import path from 'path';

const SELECTION_GRAMMAR_FILE_PATH = path.resolve('./src/selection/SelectionAutoComplete.g4');
execSync(`antlr4ts -visitor -o ./src/selection/generated ${SELECTION_GRAMMAR_FILE_PATH}`);

const files = [
  'SelectionAutoCompleteLexer.ts',
  'SelectionAutoCompleteListener.ts',
  'SelectionAutoCompleteParser.ts',
  'SelectionAutoCompleteVisitor.ts',
];

files.forEach((file) => {
  execSync(`yarn prettier ./src/selection/generated/${file} --write`);
});
