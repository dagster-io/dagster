import {execSync} from 'child_process';
import path from 'path';

const OP_SELECTION_GRAMMAR_FILE_PATH = path.resolve('./src/op-selection/OpSelection.g4');
execSync(`antlr4ts -visitor -o ./src/op-selection/generated ${OP_SELECTION_GRAMMAR_FILE_PATH}`);

const files = [
  'OpSelectionLexer.ts',
  'OpSelectionListener.ts',
  'OpSelectionParser.ts',
  'OpSelectionVisitor.ts',
];

files.forEach((file) => {
  execSync(`yarn prettier ./src/op-selection/generated/${file} --write`);
});
