import {execFileSync} from 'child_process';
import path from 'path';

const JOB_SELECTION_GRAMMAR_FILE_PATH = path.resolve('./src/job-selection/JobSelection.g4');
execFileSync('antlr4ng', [
  '-Dlanguage=TypeScript',
  '-visitor',
  '-o',
  './src/job-selection/generated',
  JOB_SELECTION_GRAMMAR_FILE_PATH,
]);

const files = [
  'JobSelectionLexer.ts',
  'JobSelectionListener.ts',
  'JobSelectionParser.ts',
  'JobSelectionVisitor.ts',
];

files.forEach((file) => {
  execFileSync(
    'yarn',
    ['prettier', '--log-level', 'silent', '--write', `./src/job-selection/generated/${file}`],
    {
      stdio: 'inherit',
    },
  );
});
