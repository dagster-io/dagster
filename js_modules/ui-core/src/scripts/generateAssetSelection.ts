// Regenerates the TypeScript ANTLR parser from AssetSelection.g4.
//
// If you added a new `attributeExpr` alternative to the grammar, also update:
//   - ../shared/asset-selection/AntlrAssetSelectionVisitor.ts (client-side eval)
//   - ./AssetSelectionSupplementaryDataVisitor.tsx (if it needs supplementary data)
//   - dagster-cloud/js_modules/app-cloud/src/asset-selection/BackendUnsupportedSelectionVisitor.tsx
//     -- add the new context to the allowlist ONLY if the backend can resolve it
//        (i.e., the AssetSelection subclass implements resolve_inner against
//        BaseAssetGraph). Otherwise leave it out and the front-end will resolve
//        the selection client-side before calling the Insights backend.
// See python_modules/dagster/dagster/_core/definitions/antlr_asset_selection/README.md.
import {execFileSync} from 'child_process';
import path from 'path';

const ASSET_SELECTION_GRAMMAR_FILE_PATH = path.resolve(
  '../../python_modules/dagster/dagster/_core/definitions/antlr_asset_selection/AssetSelection.g4',
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
