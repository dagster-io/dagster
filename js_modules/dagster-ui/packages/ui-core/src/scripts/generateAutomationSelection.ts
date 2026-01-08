import {execSync} from 'child_process';
import path from 'path';

const AUTOMATION_SELECTION_GRAMMAR_FILE_PATH = path.resolve(
  './src/automation-selection/AutomationSelection.g4',
);
execSync(
  `antlr4ng -Dlanguage=TypeScript -visitor -o ./src/automation-selection/generated ${AUTOMATION_SELECTION_GRAMMAR_FILE_PATH}`,
);

const files = [
  'AutomationSelectionLexer.ts',
  'AutomationSelectionListener.ts',
  'AutomationSelectionParser.ts',
  'AutomationSelectionVisitor.ts',
];

files.forEach((file) => {
  execSync(
    `yarn prettier --log-level silent --write ./src/automation-selection/generated/${file}`,
    {
      stdio: 'inherit',
    },
  );
});
