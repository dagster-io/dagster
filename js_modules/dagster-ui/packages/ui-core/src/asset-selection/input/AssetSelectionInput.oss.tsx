import {useAssetSelectionAutoCompleteProvider as defaultUseAssetSelectionAutoCompleteProvider} from 'shared/asset-selection/input/useAssetSelectionAutoCompleteProvider.oss';

import {assetSelectionSyntaxSupportedAttributes, unsupportedAttributeMessages} from './util';
import {AssetGraphQueryItem} from '../../asset-graph/useAssetGraphData';
import {SyntaxError} from '../../selection/CustomErrorListener';
import {SelectionAutoCompleteProvider} from '../../selection/SelectionAutoCompleteProvider';
import {SelectionAutoCompleteInput} from '../../selection/SelectionInput';
import {createSelectionLinter} from '../../selection/createSelectionLinter';
import {AssetSelectionLexer} from '../generated/AssetSelectionLexer';
import {AssetSelectionParser} from '../generated/AssetSelectionParser';

export interface AssetSelectionInputProps {
  assets: AssetGraphQueryItem[];
  value: string;
  onChange: (value: string) => void;
  linter?: (content: string) => SyntaxError[];
  useAssetSelectionAutoComplete?: (
    assets: AssetGraphQueryItem[],
  ) => Pick<SelectionAutoCompleteProvider, 'useAutoComplete'>;
}

const defaultLinter = createSelectionLinter({
  Lexer: AssetSelectionLexer,
  Parser: AssetSelectionParser,
  supportedAttributes: assetSelectionSyntaxSupportedAttributes,
  unsupportedAttributeMessages,
});

export const AssetSelectionInput = ({
  value,
  onChange,
  assets,
  linter = defaultLinter,
  useAssetSelectionAutoComplete = defaultUseAssetSelectionAutoCompleteProvider,
}: AssetSelectionInputProps) => {
  const {useAutoComplete} = useAssetSelectionAutoComplete(assets);

  return (
    <SelectionAutoCompleteInput
      id="asset-selection-input"
      useAutoComplete={useAutoComplete}
      placeholder="Search and filter assets"
      linter={linter}
      value={value}
      onChange={onChange}
    />
  );
};
