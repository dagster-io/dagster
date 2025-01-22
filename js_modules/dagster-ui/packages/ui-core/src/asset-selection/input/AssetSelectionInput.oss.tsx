import {Icons} from '@dagster-io/ui-components';
import {Linter} from 'codemirror/addon/lint/lint';
import {useMemo} from 'react';
import {
  AssetSelectionLexer,
  AssetSelectionParser,
} from 'shared/asset-selection/AssetSelectionAntlr.oss';
import {createUseAssetSelectionAutoComplete} from 'shared/asset-selection/input/useAssetSelectionAutoComplete.oss';
import styled from 'styled-components';

import {AssetGraphQueryItem} from '../../asset-graph/useAssetGraphData';
import {SelectionAutoCompleteInput, iconStyle} from '../../selection/SelectionInput';
import {createSelectionLinter} from '../../selection/createSelectionLinter';
import {placeholderTextForItems} from '../../ui/GraphQueryInput';

import 'codemirror/addon/edit/closebrackets';
import 'codemirror/lib/codemirror.css';
import 'codemirror/addon/hint/show-hint';
import 'codemirror/addon/hint/show-hint.css';

import 'codemirror/addon/lint/lint.css';
import 'codemirror/addon/display/placeholder';

interface AssetSelectionInputProps {
  assets: AssetGraphQueryItem[];
  value: string;
  onChange: (value: string) => void;
  linter?: Linter<any>;
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
}: AssetSelectionInputProps) => {
  const useAssetSelectionAutoComplete = useMemo(
    () => createUseAssetSelectionAutoComplete(assets),
    [assets],
  );

  return (
    <WrapperDiv>
      <SelectionAutoCompleteInput
        id="asset-selection-input"
        useAutoComplete={useAssetSelectionAutoComplete}
        placeholder={placeholderTextForItems('Type an asset subset…', assets)}
        linter={linter}
        value={value}
        onChange={onChange}
      />
    </WrapperDiv>
  );
};

export const WrapperDiv = styled.div`
  .attribute-owner {
    ${iconStyle(Icons.owner.src)};
  }
  .attribute-tag {
    ${iconStyle(Icons.tag.src)};
  }
  .attribute-key_substring,
  .attribute-key {
    ${iconStyle(Icons.asset.src)};
  }
  .attribute-group {
    ${iconStyle(Icons.asset_group.src)};
  }
  .attribute-code_location {
    ${iconStyle(Icons.code_location.src)};
  }
  .attribute-kind {
    ${iconStyle(Icons.compute_kind.src)};
  }
`;
