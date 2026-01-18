import {execFileSync} from 'child_process';
import path from 'path';

const ASSET_SELECTION_GRAMMAR_FILE_PATH = path.resolve(
  '../../../../python_modules/dagster/dagster/_core/definitions/antlr_asset_selection/AssetSelection.g4',
);
execFileSync('antlr4ng', [
  '-Dlanguage=TypeScript',
  '-visitor',
  '-o',
  './src/asset-selection/generated',
  ASSET_SELECTION_GRAMMAR_FILE_PATH,
]);

const files = [
  'AssetSelectionLexer.ts',
  'AssetSelectionListener.ts',
  'AssetSelectionParser.ts',
  'AssetSelectionVisitor.ts',
];

files.forEach((file) => {
  execFileSync('yarn', ['prettier', `./src/asset-selection/generated/${file}`, '--write']);
});
