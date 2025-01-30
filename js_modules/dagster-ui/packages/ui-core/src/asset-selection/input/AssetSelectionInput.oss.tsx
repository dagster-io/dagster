import type {Linter} from 'codemirror/addon/lint/lint';
import {
  AssetSelectionLexer,
  AssetSelectionParser,
} from 'shared/asset-selection/AssetSelectionAntlr.oss';
import {useAssetSelectionAutoCompleteProvider as defaultUseAssetSelectionAutoCompleteProvider} from 'shared/asset-selection/input/useAssetSelectionAutoCompleteProvider.oss';

import {AssetGraphQueryItem} from '../../asset-graph/useAssetGraphData';
import {SelectionAutoCompleteProvider} from '../../selection/SelectionAutoCompleteProvider';
import {SelectionAutoCompleteInput} from '../../selection/SelectionInput';
import {createSelectionLinter} from '../../selection/createSelectionLinter';

interface AssetSelectionInputProps {
  assets: AssetGraphQueryItem[];
  value: string;
  onChange: (value: string) => void;
  linter?: Linter<any>;
  useAssetSelectionAutoCompleteProvider?: (
    assets: AssetGraphQueryItem[],
  ) => SelectionAutoCompleteProvider;
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
  useAssetSelectionAutoCompleteProvider = defaultUseAssetSelectionAutoCompleteProvider,
}: AssetSelectionInputProps) => {
  const SelectionAutoCompleteProvider = useAssetSelectionAutoCompleteProvider(assets);

  return (
    <SelectionAutoCompleteInput
      id="asset-selection-input"
      SelectionAutoCompleteProvider={SelectionAutoCompleteProvider}
      placeholder="Search and filter assets"
      linter={linter}
      value={value}
      onChange={onChange}
    />
  );
};
