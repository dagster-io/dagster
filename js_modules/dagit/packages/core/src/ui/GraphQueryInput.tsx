// eslint-disable-next-line no-restricted-imports
import {Intent, PopoverPosition} from '@blueprintjs/core';
import {
  Box,
  Button,
  Checkbox,
  Colors,
  Icon,
  MenuItem,
  Menu,
  Popover,
  TextInput,
  Tooltip,
} from '@dagster-io/ui';
import isEqual from 'lodash/isEqual';
import uniq from 'lodash/uniq';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {filterByQuery, GraphQueryItem} from '../app/GraphQueryImpl';
import {dynamicKeyWithoutIndex, isDynamicStep} from '../gantt/DynamicStepSupport';
import {GraphExplorerSolidHandleFragment_solid} from '../pipelines/types/GraphExplorerSolidHandleFragment';
import {workspacePipelinePath} from '../workspace/workspacePath';

interface GraphQueryInputProps {
  intent?: Intent;
  items: GraphQueryItem[];
  value: string;
  placeholder: string;
  autoFocus?: boolean;
  presets?: {name: string; value: string}[];
  width?: string | number;
  popoverPosition?: PopoverPosition;
  className?: string;
  disabled?: boolean;

  linkToPreview?: {
    repoName: string;
    repoLocation: string;
    pipelineName: string;
    isJob: boolean;
  };

  flattenGraphsEnabled?: boolean;
  flattenGraphs?: boolean;
  setFlattenGraphs?: () => void;
  onChange: (value: string) => void;
  onKeyDown?: (e: React.KeyboardEvent<any>) => void;
  onFocus?: () => void;
  onBlur?: (value: string) => void;
  autoApplyChanges?: boolean;
}

interface ActiveSuggestionInfo {
  text: string;
  idx: number;
}

interface SuggestionItem {
  name: string;
  isGraph: boolean;
}

/** Generates placeholder text for the solid query box that includes a
 * practical example from the current DAG by finding the solid with the highest
 * number of immediate input or output connections and randomly highlighting
 * either the ++solid or solid++ or solid+* syntax.
 */
const placeholderTextForItems = (base: string, items: GraphQueryItem[]) => {
  const seed = items.length % 3;

  let placeholder = base;
  if (items.length === 0) {
    return placeholder;
  }

  const ranked = items.map<{
    incount: number;
    outcount: number;
    name: string;
  }>((s) => ({
    incount: s.inputs.reduce((sum, o) => sum + o.dependsOn.length, 0),
    outcount: s.outputs.reduce((sum, o) => sum + o.dependedBy.length, 0),
    name: s.name,
  }));

  if (seed === 0) {
    const example = ranked.sort((a, b) => b.outcount - a.outcount)[0];
    placeholder = `${placeholder} (ex: ${example!.name}+*)`;
  } else if (seed === 1) {
    const example = ranked.sort((a, b) => b.outcount - a.outcount)[0];
    placeholder = `${placeholder} (ex: ${example!.name}+)`;
  } else if (seed === 2) {
    const example = ranked.sort((a, b) => b.incount - a.incount)[0];
    placeholder = `${placeholder} (ex: ++${example!.name})`;
  }
  return placeholder;
};

const intentToStrokeColor = (intent: Intent | undefined) => {
  switch (intent) {
    case 'danger':
      return Colors.Red500;
    case 'success':
      return Colors.Green500;
    case 'warning':
      return Colors.Yellow500;
    case 'none':
    case 'primary':
    default:
      return Colors.Gray300;
  }
};

const buildSuggestions = (
  lastElementName: string,
  items: GraphQueryItem[] | GraphExplorerSolidHandleFragment_solid[],
  suffix: string,
) => {
  const available: SuggestionItem[] = items.map((item) => {
    const solidItem = item as GraphExplorerSolidHandleFragment_solid;
    const isGraph =
      solidItem.definition && solidItem.definition.__typename === 'CompositeSolidDefinition';

    return {name: item.name, isGraph};
  });

  for (const item of available) {
    if (isDynamicStep(item.name)) {
      available.push({name: dynamicKeyWithoutIndex(item.name), isGraph: item.isGraph});
    }
  }

  const lastElementLower = lastElementName?.toLowerCase();
  const matching =
    lastElementLower && !suffix
      ? uniq(available)
          .sort()
          .filter((n) => n.name.toLowerCase().startsWith(lastElementLower))
      : [];

  // No need to show a match if our string exactly matches the one suggestion.
  if (matching.length === 1 && matching[0].name.toLowerCase() === lastElementLower) {
    return [];
  }

  return matching;
};

export const GraphQueryInput = React.memo(
  React.forwardRef((props: GraphQueryInputProps, ref) => {
    const [active, setActive] = React.useState<ActiveSuggestionInfo | null>(null);
    const [focused, setFocused] = React.useState<boolean>(false);
    const [pendingValue, setPendingValue] = React.useState<string>(props.value);
    const inputRef = React.useRef<HTMLInputElement>(null);
    const flattenGraphsEnabled = props.flattenGraphsEnabled || false;

    React.useEffect(() => {
      // props.value is our source of truth, but we hold "un-committed" changes in
      // pendingValue while the field is being edited. Ensure the pending value
      // is synced whenever props.value changes.
      setPendingValue(props.value);
    }, [props.value]);

    const lastClause = /(\*?\+*)([\w\d\[\]>_\/-]+)(\+*\*?)$/.exec(pendingValue);

    const [, prefix, lastElementName, suffix] = lastClause || [];
    const suggestions = React.useMemo(
      () => buildSuggestions(lastElementName, props.items, suffix),
      [lastElementName, props.items, suffix],
    );

    const onConfirmSuggestion = (suggestion: string) => {
      const preceding = lastClause ? pendingValue.substr(0, lastClause.index) : '';
      setPendingValue(preceding + prefix + `"${suggestion}"` + suffix);
    };

    React.useEffect(() => {
      if (!active) {
        return;
      }
      // Relocate the currently active item in the latest suggestions list
      const pos = suggestions.map((a) => a.name).findIndex((a) => a === active.text);

      // The new index is the index of the active item, or whatever item
      // is now at it's location if it's gone, bounded to the array.
      let nextIdx = pos !== -1 ? pos : active.idx;
      nextIdx = Math.max(0, Math.min(suggestions.length - 1, nextIdx));
      if (!suggestions[nextIdx]) {
        return;
      }
      const nextText = suggestions[nextIdx].name;

      if (nextIdx !== active.idx || nextText !== active.text) {
        setActive({text: nextText, idx: nextIdx});
      }
    }, [active, suggestions]);

    React.useImperativeHandle(ref, () => ({
      focus() {
        if (inputRef.current) {
          inputRef.current.focus();
        }
      },
    }));

    const onKeyDown = (e: React.KeyboardEvent<any>) => {
      if (e.key === 'Enter' || e.key === 'Return' || e.key === 'Tab') {
        if (active && active.text) {
          onConfirmSuggestion(active.text);
          e.preventDefault();
          e.stopPropagation();
        } else {
          e.currentTarget.blur();
        }
        setActive(null);
      }

      // The up/down arrow keys shift selection in the dropdown.
      // Note: The first down arrow press activates the first item.
      const shift = {ArrowDown: 1, ArrowUp: -1}[e.key];
      if (shift && suggestions.length > 0) {
        e.preventDefault();
        let idx = (active ? active.idx : -1) + shift;
        idx = Math.max(0, Math.min(idx, suggestions.length - 1));
        setActive({text: suggestions[idx].name, idx});
      }

      props.onKeyDown?.(e);
    };

    const OpSelectionWrapperDivRef = React.useRef<HTMLDivElement>(null);

    React.useEffect(() => {
      const clickListener = (event: MouseEvent) => {
        const OpSelectionWrapperDivElement = OpSelectionWrapperDivRef.current;
        const inputElement = inputRef.current;
        const {target} = event;

        if (!flattenGraphsEnabled) {
          return;
        }
        // Make TypeScript happy
        if (
          OpSelectionWrapperDivElement == null ||
          inputElement == null ||
          !(target instanceof Node)
        ) {
          return;
        }

        // `true` if user clicked on either the `OpSelectionWrapperDivElement` itself, or its descendant
        const shouldWrapperGetFocus = OpSelectionWrapperDivElement.contains(target);
        setFocused(shouldWrapperGetFocus);

        const shouldTextInputGetFocus = inputElement.contains(target);
        if (shouldTextInputGetFocus) {
          inputElement.focus();
        }
      };

      document.addEventListener('click', clickListener);

      return () => {
        document.removeEventListener('click', clickListener);
      };
    }, [flattenGraphsEnabled]);

    const uncomitted = (pendingValue || '*') !== (props.value || '*');
    const flattenGraphsFlag = props.flattenGraphs ? '!' : '';

    const opCountInfo = props.linkToPreview && (
      <OpCountWrap $hasWrap={flattenGraphsEnabled}>
        {`${filterByQuery(props.items, pendingValue).all.length} matching ops`}
        <Link
          target="_blank"
          style={{display: 'flex', alignItems: 'center', gap: 4}}
          onMouseDown={(e) => e.currentTarget.click()}
          to={workspacePipelinePath({
            ...props.linkToPreview,
            pipelineName: `${props.linkToPreview.pipelineName}~${flattenGraphsFlag}${pendingValue}`,
          })}
        >
          Graph Preview <Icon color={Colors.Link} name="open_in_new" />
        </Link>
      </OpCountWrap>
    );

    return (
      <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
        <Popover
          enforceFocus={!flattenGraphsEnabled} // Defer focus to be manually managed
          isOpen={focused}
          position={props.popoverPosition || 'top-left'}
          content={
            suggestions.length ? (
              <Menu style={{width: props.width || '24vw'}}>
                {suggestions.slice(0, 15).map((suggestion) => (
                  <MenuItem
                    icon={suggestion.isGraph ? 'job' : 'op'}
                    key={suggestion.name}
                    text={suggestion.name}
                    active={active ? active.text === suggestion.name : false}
                    onMouseDown={(e: React.MouseEvent<any>) => {
                      e.preventDefault();
                      e.stopPropagation();
                      onConfirmSuggestion(suggestion.name);
                    }}
                  />
                ))}
              </Menu>
            ) : (
              <div />
            )
          }
        >
          <div style={{position: 'relative'}} ref={OpSelectionWrapperDivRef}>
            <TextInput
              disabled={props.disabled}
              value={pendingValue}
              icon="op_selector"
              strokeColor={intentToStrokeColor(props.intent)}
              autoFocus={props.autoFocus}
              placeholder={placeholderTextForItems(props.placeholder, props.items)}
              onChange={(e: React.ChangeEvent<any>) => {
                setPendingValue(e.target.value);
                props.autoApplyChanges && props.onChange(e.target.value);
              }}
              onFocus={() => {
                if (!flattenGraphsEnabled) {
                  // Defer focus to be manually managed
                  setFocused(true);
                }
                props.onFocus?.();
              }}
              onBlur={() => {
                if (!flattenGraphsEnabled) {
                  // Defer focus to be manually managed
                  setFocused(false);
                }
                props.onChange(pendingValue);
                props.onBlur?.(pendingValue);
              }}
              onKeyDown={onKeyDown}
              style={{
                width: props.width || '24vw',
                paddingRight: focused && uncomitted ? 55 : '',
              }}
              className={props.className}
              ref={inputRef}
            />
            {focused && uncomitted && <EnterHint>Enter</EnterHint>}
            {focused &&
              props.linkToPreview &&
              (flattenGraphsEnabled ? (
                <OpInfoWrap>
                  <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
                    <Checkbox
                      label="Flatten subgraphs"
                      checked={props.flattenGraphs ?? false}
                      onChange={() => {
                        props.setFlattenGraphs?.();
                      }}
                      format="switch"
                    />
                    <Tooltip
                      content="Flatten subgraphs to select ops within nested graphs"
                      placement="right"
                    >
                      <Icon name="info" color={Colors.Gray500} />
                    </Tooltip>
                  </Box>
                  {opCountInfo}
                </OpInfoWrap>
              ) : (
                opCountInfo
              ))}
          </div>
        </Popover>
        {props.presets &&
          (props.presets.find((p) => p.value === pendingValue) ? (
            <Button
              icon={<Icon name="layers" />}
              rightIcon={<Icon name="cancel" />}
              onClick={() => props.onChange('*')}
              intent="none"
            />
          ) : (
            <Popover
              position="top"
              content={
                <Menu>
                  {props.presets.map((preset) => (
                    <MenuItem
                      key={preset.name}
                      text={preset.name}
                      onMouseDown={(e: React.MouseEvent<any>) => {
                        e.preventDefault();
                        e.stopPropagation();
                        props.onChange(preset.value);
                      }}
                    />
                  ))}
                </Menu>
              }
            >
              <Button
                icon={<Icon name="layers" />}
                rightIcon={<Icon name="expand_less" />}
                intent="none"
              />
            </Popover>
          ))}
      </Box>
    );
  }),

  (prevProps, nextProps) =>
    prevProps.items === nextProps.items &&
    prevProps.width === nextProps.width &&
    prevProps.value === nextProps.value &&
    isEqual(prevProps.presets, nextProps.presets),
);

const OpInfoWrap = styled.div`
  width: 350px;
  padding: 10px 16px 10px 16px;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  position: absolute;
  top: 100%;
  margin-top: 2px;
  font-size: 0.85rem;
  background: ${Colors.White};
  color: ${Colors.Gray600};
  box-shadow: 1px 1px 3px rgba(0, 0, 0, 0.2);
  z-index: 2;
  left: 0;
`;

const OpCountWrap = styled(OpInfoWrap)<{$hasWrap: boolean}>`
  margin-top: ${(p) => (p.$hasWrap ? 0 : 2)}px;
`;

const EnterHint = styled.div`
  position: absolute;
  right: 6px;
  top: 5px;
  border-radius: 5px;
  border: 1px solid ${Colors.Gray500};
  background: ${Colors.White};
  font-weight: 500;
  font-size: 12px;
  color: ${Colors.Gray500};
  padding: 2px 6px;
`;
