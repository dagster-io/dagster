import {useCallback} from 'react';
import {useAssetSelectionAutoCompleteProvider as defaultUseAssetSelectionAutoCompleteProvider} from 'shared/asset-selection/input/useAssetSelectionAutoCompleteProvider.oss';

import {assetSelectionSyntaxSupportedAttributes, unsupportedAttributeMessages} from './util';
import {AssetGraphQueryItem} from '../../asset-graph/useAssetGraphData';
import {SyntaxError} from '../../selection/CustomErrorListener';
import {SelectionAutoCompleteProvider} from '../../selection/SelectionAutoCompleteProvider';
import {SelectionAutoCompleteInput} from '../../selection/SelectionInput';
import {createSelectionLinter} from '../../selection/createSelectionLinter';
import {AssetSelectionLexer} from '../generated/AssetSelectionLexer';
import {AssetSelectionParser} from '../generated/AssetSelectionParser';
import {isUnmatchedValueQuery} from '../isUnmatchedValueQuery';
import {parseAssetSelectionQuery} from '../parseAssetSelectionQuery';

export interface AssetSelectionInputProps {
  assets: AssetGraphQueryItem[];
  value: string;
  onChange: (value: string) => void;
  onErrorStateChange?: (errors: SyntaxError[]) => void;
  linter?: (content: string) => SyntaxError[];
  useAssetSelectionAutoComplete?: (
    assets: AssetGraphQueryItem[],
  ) => Pick<SelectionAutoCompleteProvider, 'useAutoComplete'>;
  saveOnBlur?: boolean;
}

const defaultLinter = createSelectionLinter({
  Lexer: AssetSelectionLexer,
  Parser: AssetSelectionParser,
  supportedAttributes: assetSelectionSyntaxSupportedAttributes,
  unsupportedAttributeMessages,
});

export const AssetSelectionInput = ({
  value,
  onChange: _onChange,
  assets,
  linter = defaultLinter,
  useAssetSelectionAutoComplete = defaultUseAssetSelectionAutoCompleteProvider,
  saveOnBlur = false,
  onErrorStateChange,
}: AssetSelectionInputProps) => {
  const {useAutoComplete} = useAssetSelectionAutoComplete(assets);

  const onChange = useCallback(
    (value: string) => {
      if (parseAssetSelectionQuery([], value) instanceof Error && isUnmatchedValueQuery(value)) {
        _onChange(`key:"*${value}*"`);
      } else {
        _onChange(value);
      }
    },
    [_onChange],
  );

  return (
    <SelectionAutoCompleteInput
      id="asset-selection-input"
      useAutoComplete={useAutoComplete}
      placeholder="Search and filter assets"
      linter={linter}
      value={value}
      onChange={onChange}
      saveOnBlur={saveOnBlur}
      onErrorStateChange={onErrorStateChange}
    />
  );
};
