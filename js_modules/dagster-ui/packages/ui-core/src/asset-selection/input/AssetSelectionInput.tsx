import type {Linter} from 'codemirror/addon/lint/lint';
import {useMemo} from 'react';
import {
  AssetSelectionLexer,
  AssetSelectionParser,
} from 'shared/asset-selection/AssetSelectionAntlr.oss';
import {createUseAssetSelectionAutoComplete as defaultCreateUseAssetSelectionAutoComplete} from 'shared/asset-selection/input/useAssetSelectionAutoComplete.oss';

import {AssetGraphQueryItem} from '../../asset-graph/useAssetGraphData';
import {SelectionAutoCompleteInput} from '../../selection/SelectionInput';
import {createSelectionLinter} from '../../selection/createSelectionLinter';

interface AssetSelectionInputProps {
  assets: AssetGraphQueryItem[];
  value: string;
  onChange: (value: string) => void;
  linter?: Linter<any>;
  createUseAssetSelectionAutoComplete?: typeof defaultCreateUseAssetSelectionAutoComplete;
}

const defaultLinter = createSelectionLinter({
  Lexer: AssetSelectionLexer,
  Parser: AssetSelectionParser,
});

export const AssetSelectionInput = ({
  value,
  onChange,
  assets,
  linter = defaultLinter,
  createUseAssetSelectionAutoComplete = defaultCreateUseAssetSelectionAutoComplete,
}: AssetSelectionInputProps) => {
  const useAssetSelectionAutoComplete = useMemo(
    () => createUseAssetSelectionAutoComplete(assets),
    [assets, createUseAssetSelectionAutoComplete],
  );

  return (
    <SelectionAutoCompleteInput
      id="asset-selection-input"
      useAutoComplete={useAssetSelectionAutoComplete}
      placeholder="Search and filter assets"
      linter={linter}
      value={value}
      onChange={onChange}
    />
  );
};
