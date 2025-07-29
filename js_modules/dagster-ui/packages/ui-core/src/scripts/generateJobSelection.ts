import {execSync} from 'child_process';
import path from 'path';

const JOB_SELECTION_GRAMMAR_FILE_PATH = path.resolve('./src/job-selection/JobSelection.g4');
execSync(`antlr4ts -visitor -o ./src/job-selection/generated ${JOB_SELECTION_GRAMMAR_FILE_PATH}`);

const files = [
  'JobSelectionLexer.ts',
  'JobSelectionListener.ts',
  'JobSelectionParser.ts',
  'JobSelectionVisitor.ts',
];

files.forEach((file) => {
  execSync(`yarn prettier --log-level silent --write ./src/job-selection/generated/${file}`, {
    stdio: 'inherit',
  });
});
