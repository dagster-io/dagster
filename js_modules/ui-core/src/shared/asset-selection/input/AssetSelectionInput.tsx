import {useAssetSelectionAutoCompleteProvider as defaultUseAssetSelectionAutoCompleteProvider} from '@shared/asset-selection/input/useAssetSelectionAutoCompleteProvider';

import {AssetGraphQueryItem} from '../../../asset-graph/types';
import {AssetSelectionLexer} from '../../../asset-selection/generated/AssetSelectionLexer';
import {AssetSelectionParser} from '../../../asset-selection/generated/AssetSelectionParser';
import {
  ASSET_SELECTION_RECENTS_KEY,
  assetSelectionSyntaxSupportedAttributes,
  unsupportedAttributeMessages,
} from '../../../asset-selection/input/util';
import {SyntaxError} from '../../../selection/CustomErrorListener';
import {SelectionAutoCompleteProvider} from '../../../selection/SelectionAutoCompleteProvider';
import {SelectionAutoCompleteInput} from '../../../selection/SelectionInput';
import {createSelectionLinter} from '../../../selection/createSelectionLinter';

export interface AssetSelectionInputProps {
  assets: AssetGraphQueryItem[];
  value: string;
  onChange?: (value: string) => void;
  onSubmit?: (value: string) => void;
  onErrorStateChange?: (errors: SyntaxError[]) => void;
  linter?: (content: string) => SyntaxError[];
  useAssetSelectionAutoComplete?: (
    assets: AssetGraphQueryItem[],
  ) => Pick<SelectionAutoCompleteProvider, 'useAutoComplete'>;
  saveOnBlur?: boolean;
  placeholder?: string;
  className?: string;
  showRecentSearches?: boolean;
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
  onSubmit,
  assets,
  linter = defaultLinter,
  useAssetSelectionAutoComplete = defaultUseAssetSelectionAutoCompleteProvider,
  saveOnBlur = false,
  onErrorStateChange,
  placeholder = 'Search and filter assets',
  className,
  showRecentSearches = false,
}: AssetSelectionInputProps) => {
  const {useAutoComplete} = useAssetSelectionAutoComplete(assets);

  return (
    <SelectionAutoCompleteInput
      wildcardAttributeName="key"
      id="asset-selection-input"
      useAutoComplete={useAutoComplete}
      placeholder={placeholder}
      linter={linter}
      value={value}
      onChange={onChange}
      onSubmit={onSubmit}
      saveOnBlur={saveOnBlur}
      onErrorStateChange={onErrorStateChange}
      recentSearchesKey={showRecentSearches ? ASSET_SELECTION_RECENTS_KEY : undefined}
      className={className}
    />
  );
};
