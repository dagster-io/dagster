import {Colors, Icon, Icons} from '@dagster-io/ui-components';
import CodeMirror, {Editor, HintFunction} from 'codemirror';
import {useLayoutEffect, useMemo, useRef} from 'react';
import styled, {createGlobalStyle, css} from 'styled-components';

import {lintAssetSelection} from './AssetSelectionLinter';
import {assertUnreachable} from '../../app/Util';
import {AssetGraphQueryItem} from '../../asset-graph/useAssetGraphData';
import {useUpdatingRef} from '../../hooks/useUpdatingRef';
import {createSelectionHint} from '../../selection/SelectionAutoComplete';
import {
  SelectionAutoCompleteInputCSS,
  applyStaticSyntaxHighlighting,
} from '../../selection/SelectionAutoCompleteHighlighter';
import {placeholderTextForItems} from '../../ui/GraphQueryInput';
import {buildRepoPathForHuman} from '../../workspace/buildRepoAddress';

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

export const AssetSelectionInput = ({value, onChange, assets}: AssetSelectionInputProps) => {
  const editorRef = useRef<HTMLDivElement>(null);
  const cmInstance = useRef<CodeMirror.Editor | null>(null);

  const currentValueRef = useRef(value);

  const hintRef = useUpdatingRef(
    useMemo(() => {
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
            tagNamesSet.add(`${tag.key}=${tag.value}`);
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

      return createSelectionHint(
        'key',
        {
          key: assetNames,
          tag: tagNames,
          owner: owners,
          group: groups,
          kind: kinds,
          code_location: codeLocations,
        },
        FUNCTIONS,
      );
    }, [assets]),
  );

  useLayoutEffect(() => {
    if (editorRef.current && !cmInstance.current) {
      cmInstance.current = CodeMirror(editorRef.current, {
        value,
        mode: 'assetSelection',
        lineNumbers: false,
        lineWrapping: false,
        scrollbarStyle: 'native',
        autoCloseBrackets: true,
        lint: {
          getAnnotations: lintAssetSelection,
          async: false,
        },
        placeholder: placeholderTextForItems('Type an asset subset…', assets),
        extraKeys: {
          'Ctrl-Space': 'autocomplete',
          Tab: (cm: Editor) => {
            cm.replaceSelection('  ', 'end');
          },
        },
      });

      cmInstance.current.setSize('100%', 20);

      // Enforce single line by preventing newlines
      cmInstance.current.on('beforeChange', (_instance: Editor, change) => {
        if (change.text.some((line) => line.includes('\n'))) {
          change.cancel();
        }
      });

      cmInstance.current.on('change', (instance: Editor, change) => {
        const newValue = instance.getValue().replace(/\s+/g, ' ');
        currentValueRef.current = newValue;
        onChange(newValue);

        if (change.origin === 'complete' && change.text[0]?.endsWith('()')) {
          // Set cursor inside the right parenthesis
          const cursor = instance.getCursor();
          instance.setCursor({...cursor, ch: cursor.ch - 1});
        }
      });

      cmInstance.current.on('inputRead', (instance: Editor) => {
        showHint(instance, hintRef.current);
      });

      cmInstance.current.on('cursorActivity', (instance: Editor) => {
        applyStaticSyntaxHighlighting(instance);
        showHint(instance, hintRef.current);
      });

      requestAnimationFrame(() => {
        if (!cmInstance.current) {
          return;
        }

        applyStaticSyntaxHighlighting(cmInstance.current);
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update CodeMirror when value prop changes
  useLayoutEffect(() => {
    const noNewLineValue = value.replace('\n', ' ');
    if (cmInstance.current && cmInstance.current.getValue() !== noNewLineValue) {
      const instance = cmInstance.current;
      const cursor = instance.getCursor();
      instance.setValue(noNewLineValue);
      instance.setCursor(cursor);
      showHint(instance, hintRef.current);
    }
  }, [hintRef, value]);

  return (
    <>
      <GlobalHintStyles />
      <InputDiv
        style={{
          display: 'grid',
          gridTemplateColumns: 'auto minmax(0, 1fr) auto',
          alignItems: 'center',
        }}
      >
        <Icon name="op_selector" />
        <div ref={editorRef} />
        <Icon name="info" />
      </InputDiv>
    </>
  );
};
const iconStyle = (img: string) => css`
  &:before {
    content: ' ';
    width: 14px;
    mask-size: contain;
    mask-repeat: no-repeat;
    mask-position: center;
    mask-image: url(${img});
    background: ${Colors.accentPrimary()};
    display: inline-block;
  }
`;

const InputDiv = styled.div`
  ${SelectionAutoCompleteInputCSS}

  .attribute-owner {
    ${iconStyle(Icons.owner.src)}
  }
`;

const GlobalHintStyles = createGlobalStyle`
  .CodeMirror-hints {
    background: ${Colors.popoverBackground()};
    border: none;
    border-radius: 4px;
    padding: 8px 4px;
    .CodeMirror-hint {
      border-radius: 4px;
      font-size: 14px;
      padding: 6px 8px 6px 12px;
      color: ${Colors.textDefault()};
      &.CodeMirror-hint-active {
        background-color: ${Colors.backgroundBlue()};
        color: ${Colors.textDefault()};
      }
    }
  }
`;

function showHint(instance: Editor, hint: HintFunction) {
  requestAnimationFrame(() => {
    instance.showHint({
      hint,
      completeSingle: false,
      moveOnOverlap: true,
      updateOnCursorActivity: true,
    });
  });
}
