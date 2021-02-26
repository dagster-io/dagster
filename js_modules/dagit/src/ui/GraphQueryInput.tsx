import {gql} from '@apollo/client';
import {Button, Colors, InputGroup, Intent, Menu, MenuItem, Popover} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import isEqual from 'lodash/isEqual';
import uniq from 'lodash/uniq';
import * as React from 'react';
import styled from 'styled-components/macro';

import {GraphQueryItem} from 'src/app/GraphQueryImpl';
import {dynamicKeyWithoutIndex, isDynamicStep} from 'src/gantt/DynamicStepSupport';

interface GraphQueryInputProps {
  intent?: Intent;
  items: GraphQueryItem[];
  value: string;
  placeholder: string;
  autoFocus?: boolean;
  presets?: {name: string; value: string}[];
  width?: string | number;
  small?: boolean;
  className?: string;
  disabled?: boolean;

  onChange: (value: string) => void;
  onKeyDown?: (e: React.KeyboardEvent<any>) => void;
  onFocus?: () => void;
  onBlur?: (value: string) => void;
}

interface ActiveSuggestionInfo {
  text: string;
  idx: number;
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

export const GraphQueryInput = React.memo(
  (props: GraphQueryInputProps) => {
    const [active, setActive] = React.useState<ActiveSuggestionInfo | null>(null);
    const [focused, setFocused] = React.useState<boolean>(false);
    const [pendingValue, setPendingValue] = React.useState<string>(props.value);

    React.useEffect(() => {
      // props.value is our source of truth, but we hold "un-committed" changes in
      // pendingValue while the field is being edited. Ensure the pending value
      // is synced whenever props.value changes.
      setPendingValue(props.value);
    }, [props.value]);

    const lastClause = /(\*?\+*)([\w\d\[\]_-]+)(\+*\*?)$/.exec(pendingValue);
    let menu: JSX.Element | undefined = undefined;

    const [, prefix, lastElementName, suffix] = lastClause || [];
    const suggestions = React.useMemo(() => {
      const available = props.items.map((s) => s.name);
      for (const name of available) {
        if (isDynamicStep(name)) {
          available.push(dynamicKeyWithoutIndex(name));
        }
      }

      return lastElementName && !suffix
        ? uniq(available)
            .sort()
            .filter((n) => n.startsWith(lastElementName) && n !== lastElementName)
        : [];
    }, [lastElementName, props.items, suffix]);

    const onConfirmSuggestion = (suggestion: string) => {
      const preceding = lastClause ? pendingValue.substr(0, lastClause.index) : '';
      setPendingValue(preceding + prefix + suggestion + suffix);
    };

    if (suggestions.length && focused) {
      menu = (
        <Menu style={{width: props.width || '30vw'}}>
          {suggestions.slice(0, 15).map((suggestion) => (
            <StyledMenuItem
              key={suggestion}
              text={suggestion}
              active={active ? active.text === suggestion : false}
              onMouseDown={(e: React.MouseEvent<any>) => {
                e.preventDefault();
                e.stopPropagation();
                onConfirmSuggestion(suggestion);
              }}
            />
          ))}
        </Menu>
      );
    }

    React.useEffect(() => {
      if (!active && suggestions.length) {
        setActive({text: suggestions[0], idx: 0});
        return;
      }
      if (!active) {
        return;
      }
      // Relocate the currently active item in the latest suggestions list
      const pos = suggestions.findIndex((a) => a === active.text);

      // The new index is the index of the active item, or whatever item
      // is now at it's location if it's gone, bounded to the array.
      let nextIdx = pos !== -1 ? pos : active.idx;
      nextIdx = Math.max(0, Math.min(suggestions.length - 1, nextIdx));
      const nextText = suggestions[nextIdx];

      if (nextIdx !== active.idx || nextText !== active.text) {
        setActive({text: nextText, idx: nextIdx});
      }
    }, [active, suggestions]);

    const onKeyDown = (e: React.KeyboardEvent<any>) => {
      if (e.key === 'Enter' || e.key === 'Return' || e.key === 'Tab') {
        if (active && active.text) {
          onConfirmSuggestion(active.text);
          e.preventDefault();
          e.stopPropagation();
        }
      }

      // The up/down arrow keys shift selection in the dropdown.
      // Note: The first down arrow press activates the first item.
      const shift = {ArrowDown: 1, ArrowUp: -1}[e.key];
      if (shift && suggestions.length > 0) {
        e.preventDefault();
        let idx = (active ? active.idx : -1) + shift;
        idx = Math.max(0, Math.min(idx, suggestions.length - 1));
        setActive({text: suggestions[idx], idx});
      }

      props.onKeyDown?.(e);
    };

    const onKeyUp = (e: React.KeyboardEvent<any>) => {
      if (
        e.key === 'Enter' ||
        e.key === 'Return' ||
        e.key === 'Tab' ||
        e.key === '+' ||
        e.key === ' ' ||
        (e.key === '*' && pendingValue.length > 1) ||
        (e.key === 'Backspace' && pendingValue.length)
      ) {
        props.onChange(pendingValue);
      }
    };

    return (
      <>
        <Popover minimal={true} isOpen={menu !== undefined} position={'bottom'} content={menu}>
          <GraphQueryInputField
            small={props.small}
            disabled={props.disabled}
            intent={props.intent}
            title="graph-query-input"
            type="text"
            value={pendingValue}
            leftIcon={'send-to-graph'}
            autoFocus={props.autoFocus}
            placeholder={placeholderTextForItems(props.placeholder, props.items)}
            onChange={(e: React.ChangeEvent<any>) => setPendingValue(e.target.value)}
            onFocus={() => {
              setFocused(true);
              props.onFocus?.();
            }}
            onBlur={() => {
              setFocused(false);
              props.onChange(pendingValue);
              props.onBlur?.(pendingValue);
            }}
            onKeyDown={onKeyDown}
            onKeyUp={onKeyUp}
            style={{width: props.width || '30vw'}}
            className={props.className}
          />
        </Popover>
        {props.presets &&
          (props.presets.find((p) => p.value === pendingValue) ? (
            <Button
              style={{marginLeft: 5}}
              icon={IconNames.LAYERS}
              rightIcon={IconNames.CROSS}
              onClick={() => {
                props.onChange('*');
              }}
            />
          ) : (
            <Popover
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
                style={{marginLeft: 5}}
                icon={IconNames.LAYERS}
                rightIcon={IconNames.CARET_UP}
              />
            </Popover>
          ))}
      </>
    );
  },

  (prevProps, nextProps) =>
    prevProps.items === nextProps.items &&
    prevProps.width === nextProps.width &&
    prevProps.value === nextProps.value &&
    isEqual(prevProps.presets, nextProps.presets),
);

export const SOLID_QUERY_INPUT_SOLID_FRAGMENT = gql`
  fragment SolidQueryInputSolidFragment on Solid {
    name
    inputs {
      dependsOn {
        solid {
          name
        }
      }
    }
    outputs {
      dependedBy {
        solid {
          name
        }
      }
    }
  }
`;

const GraphQueryInputField = styled(InputGroup)`
  font-size: 14px;
  & > input {
    transition: width 100ms ease-in-out;
  }

  &.has-step {
    box-shadow: 0 0 0 2px ${Colors.GOLD3};
    border-radius: 3px;
  }
`;

const StyledMenuItem = styled(MenuItem)`
  font-size: 13px;
  line-height: 15px;
`;
