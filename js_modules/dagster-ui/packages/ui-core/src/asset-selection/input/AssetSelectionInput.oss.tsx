import {Icons} from '@dagster-io/ui-components';
import {useMemo} from 'react';
import styled from 'styled-components';

import {assertUnreachable} from '../../app/Util';
import {AssetGraphQueryItem} from '../../asset-graph/useAssetGraphData';
import {SelectionAutoCompleteInput, iconStyle} from '../../selection/SelectionAutoCompleteInput';
import {createSelectionLinter} from '../../selection/createSelectionLinter';
import {placeholderTextForItems} from '../../ui/GraphQueryInput';
import {buildRepoPathForHuman} from '../../workspace/buildRepoAddress';
import {AssetSelectionLexer} from '../generated/AssetSelectionLexer';
import {AssetSelectionParser} from '../generated/AssetSelectionParser';

import 'codemirror/addon/edit/closebrackets';
import 'codemirror/lib/codemirror.css';
import 'codemirror/addon/hint/show-hint';
import 'codemirror/addon/hint/show-hint.css';
import 'codemirror/addon/lint/lint';
import 'codemirror/addon/lint/lint.css';
import 'codemirror/addon/display/placeholder';

interface AssetSelectionInputProps {
  assets: AssetGraphQueryItem[];
  value: string;
  onChange: (value: string) => void;
}

const FUNCTIONS = ['sinks', 'roots'];

const linter = createSelectionLinter({Lexer: AssetSelectionLexer, Parser: AssetSelectionParser});

export const AssetSelectionInput = ({value, onChange, assets}: AssetSelectionInputProps) => {
  const attributesMap = useMemo(() => {
    const assetNamesSet: Set<string> = new Set();
    const tagNamesSet: Set<string> = new Set();
    const ownersSet: Set<string> = new Set();
    const groupsSet: Set<string> = new Set();
    const kindsSet: Set<string> = new Set();
    const codeLocationSet: Set<string> = new Set();

    assets.forEach((asset) => {
      assetNamesSet.add(asset.name);
      asset.node.tags.forEach((tag) => {
        if (tag.key && tag.value) {
          // We add quotes around the equal sign here because the auto-complete suggestion already wraps the entire value in quotes.
          // So wer end up with tag:"key"="value" as the final suggestion
          tagNamesSet.add(`${tag.key}"="${tag.value}`);
        } else {
          tagNamesSet.add(tag.key);
        }
      });
      asset.node.owners.forEach((owner) => {
        switch (owner.__typename) {
          case 'TeamAssetOwner':
            ownersSet.add(owner.team);
            break;
          case 'UserAssetOwner':
            ownersSet.add(owner.email);
            break;
          default:
            assertUnreachable(owner);
        }
      });
      if (asset.node.groupName) {
        groupsSet.add(asset.node.groupName);
      }
      asset.node.kinds.forEach((kind) => {
        kindsSet.add(kind);
      });
      const location = buildRepoPathForHuman(
        asset.node.repository.name,
        asset.node.repository.location.name,
      );
      codeLocationSet.add(location);
    });

    const assetNames = Array.from(assetNamesSet);
    const tagNames = Array.from(tagNamesSet);
    const owners = Array.from(ownersSet);
    const groups = Array.from(groupsSet);
    const kinds = Array.from(kindsSet);
    const codeLocations = Array.from(codeLocationSet);

    return {
      key: assetNames,
      tag: tagNames,
      owner: owners,
      group: groups,
      kind: kinds,
      code_location: codeLocations,
    };
  }, [assets]);

  return (
    <WrapperDiv>
      <SelectionAutoCompleteInput
        id="asset-selection-input"
        nameBase="key"
        attributesMap={attributesMap}
        placeholder={placeholderTextForItems('Type an asset subset…', assets)}
        functions={FUNCTIONS}
        linter={linter}
        value={value}
        onChange={onChange}
      />
    </WrapperDiv>
  );
};

const WrapperDiv = styled.div`
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
