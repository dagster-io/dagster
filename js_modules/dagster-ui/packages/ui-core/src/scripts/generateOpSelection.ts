import {execFileSync} from 'child_process';
import path from 'path';

const OP_SELECTION_GRAMMAR_FILE_PATH = path.resolve('./src/op-selection/OpSelection.g4');
execFileSync('antlr4ng', [
  '-Dlanguage=TypeScript',
  '-visitor',
  '-o',
  './src/op-selection/generated',
  OP_SELECTION_GRAMMAR_FILE_PATH,
]);

const files = [
  'OpSelectionLexer.ts',
  'OpSelectionListener.ts',
  'OpSelectionParser.ts',
  'OpSelectionVisitor.ts',
];

files.forEach((file) => {
  execFileSync('yarn', ['prettier', `./src/op-selection/generated/${file}`, '--write']);
});
