import {Box, Checkbox, Colors, IconName, Popover} from '@dagster-io/ui-components';
import {
  ComponentProps,
  Fragment,
  useContext,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from 'react';

import {FilterObject, FilterTag, FilterTagHighlightedText} from './useFilter';
import {useUpdatingRef} from '../../hooks/useUpdatingRef';
import {LaunchpadHooksContext} from '../../launchpad/LaunchpadHooksContext';

export type SetFilterValue<T> = {
  value: T;
  match: string[];
};

export type StaticBaseConfig<TValue> = {
  name: string;
  icon: IconName;
  renderLabel: (props: {value: TValue; isActive: boolean}) => JSX.Element;
  renderActiveStateLabel?: (props: {value: TValue; isActive: boolean}) => JSX.Element;
  getKey?: (value: TValue) => string;
  getStringValue: (value: TValue) => string;
  getTooltipText?: (value: TValue) => string;
  matchType?: 'any-of' | 'all-of';
};

type FilterArgs<TValue> = StaticBaseConfig<TValue> & {
  allValues: SetFilterValue<TValue>[];

  // This hook is NOT a "controlled component". Changing state only updates the component's current state.
  // To make this fully controlled you need to implement `onStateChanged` and maintain your own copy of the state.
  // The one tricky footgun is if you want to ignore (ie. cancel) a state change then you need to make a new reference
  // to the old state and pass that in.
  state?: Set<TValue> | TValue[];
  onStateChanged?: (state: Set<TValue>) => void;

  allowMultipleSelections?: boolean;
  selectAllText?: React.ReactNode;
  canSelectAll?: boolean;
  menuWidth?: number | string;
  closeOnSelect?: boolean;
};

export type StaticSetFilter<TValue> = FilterObject & {
  state: Set<TValue>;
  setState: (state: Set<TValue>) => void;
};

const selectAllSymbol = Symbol.for('useStaticSetFilter:SelectAll');

export function useStaticSetFilter<TValue>({
  name,
  icon,
  getKey,
  allValues: _unsortedValues,
  renderLabel,
  renderActiveStateLabel,
  state,
  getStringValue,
  getTooltipText,
  onStateChanged,
  menuWidth,
  allowMultipleSelections = true,
  matchType = 'any-of',
  closeOnSelect = false,
  selectAllText,
  canSelectAll = true,
}: FilterArgs<TValue>): StaticSetFilter<TValue> {
  const {StaticFilterSorter} = useContext(LaunchpadHooksContext);

  const allValues = useMemo(() => {
    const sorter = StaticFilterSorter?.[name];
    if (sorter) {
      return _unsortedValues.sort(sorter);
    }
    return _unsortedValues;
  }, [StaticFilterSorter, name, _unsortedValues]);

  // This filter can be used as both a controlled and an uncontrolled component necessitating an innerState for the uncontrolled case.
  const [innerState, setState] = useState(() => new Set(state || []));

  const isFirstRenderRef = useRef(true);

  useLayoutEffect(() => {
    if (!isFirstRenderRef.current) {
      onStateChanged?.(innerState);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [innerState]);

  useEffect(() => {
    if (!isFirstRenderRef.current) {
      setState(state ? new Set(state) : new Set());
    }
    isFirstRenderRef.current = false;
  }, [state]);

  const currentQueryRef = useRef<string>('');

  const filterObj: StaticSetFilter<TValue> = useMemo(
    () => ({
      name,
      icon,
      state: innerState,
      isActive: innerState.size > 0,
      getResults: (query) => {
        currentQueryRef.current = query;
        let results;
        if (query === '') {
          results = allValues.map(({value}, index) => ({
            label: (
              <SetFilterLabel
                value={value}
                renderLabel={renderLabel}
                filter={filterObjRef.current}
                allowMultipleSelections={allowMultipleSelections}
              />
            ),
            key: getKey?.(value) || index.toString(),
            value,
          }));
        } else {
          results = allValues
            .filter(({match}) =>
              match.some((value) => value.toLowerCase().includes(query.toLowerCase())),
            )
            .map(({value}, index) => ({
              label: (
                <SetFilterLabel
                  value={value}
                  renderLabel={renderLabel}
                  filter={filterObjRef.current}
                  allowMultipleSelections={allowMultipleSelections}
                />
              ),
              key: getKey?.(value) || index.toString(),
              value,
            }));
        }
        if (allowMultipleSelections && results.length > 1 && canSelectAll) {
          return [
            {
              label: (
                <SetFilterLabel
                  value={selectAllSymbol}
                  renderLabel={() => <>{selectAllText ?? 'Select all'}</>}
                  isForcedActive={
                    (state instanceof Set ? state.size : state?.length) === allValues.length
                  }
                  filter={filterObjRef.current}
                  allowMultipleSelections={allowMultipleSelections}
                />
              ),
              key: 'useStaticSetFilter:select-all-key',
              value: selectAllSymbol,
            },
            ...results,
          ];
        }
        return results;
      },
      onSelect: ({value, close}) => {
        const state = filterObjRef.current.state;
        if (typeof value === 'symbol' && value.toString() === selectAllSymbol.toString()) {
          let selectResults;
          if (currentQueryRef.current === '') {
            selectResults = allValues;
          } else {
            selectResults = allValues.filter(({match}) =>
              match.some((value) =>
                value.toLowerCase().includes(currentQueryRef.current.toLowerCase()),
              ),
            );
          }
          const hasAnyUnselected = selectResults.find((result) => {
            if (state instanceof Array) {
              return state.indexOf(result.value) === -1;
            } else if (state instanceof Set) {
              return !state.has(result.value);
            }
            return true;
          });
          if (hasAnyUnselected) {
            setState(new Set([...Array.from(state), ...selectResults.map(({value}) => value)]));
          } else {
            const stateCopy = new Set(state);
            selectResults.forEach(({value}) => {
              stateCopy.delete(value);
            });
            setState(stateCopy);
          }
          return;
        }
        let newState = new Set(state);
        if (newState.has(value)) {
          newState.delete(value);
        } else {
          if (!allowMultipleSelections) {
            newState = new Set([value]);
          } else {
            newState.add(value);
          }
        }
        setState(newState);
        if (closeOnSelect) {
          close();
        }
      },

      activeJSX: (
        <SetFilterActiveState
          name={name}
          state={innerState}
          getStringValue={getStringValue}
          getTooltipText={getTooltipText}
          renderLabel={renderActiveStateLabel || renderLabel}
          onRemove={() => {
            setState(new Set());
          }}
          icon={icon}
          matchType={matchType}
        />
      ),
      setState,
      menuWidth,
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [
      name,
      icon,
      innerState,
      getStringValue,
      renderActiveStateLabel,
      renderLabel,
      matchType,
      allValues,
      allowMultipleSelections,
      getKey,
      selectAllText,
    ],
  );
  const filterObjRef = useUpdatingRef(filterObj);
  return filterObj;
}

const MAX_VALUES_TO_SHOW = 3;

export function SetFilterActiveState({
  name,
  state,
  icon,
  getStringValue,
  onRemove,
  renderLabel,
  matchType = 'any-of',
  getTooltipText,
  theme,
}: {
  name: string;
  icon: IconName;
  state: Set<any> | any[];
  getStringValue: (value: any) => string;
  getTooltipText?: ((value: any) => string) | undefined;
  onRemove?: () => void;
  renderLabel: (value: any) => JSX.Element;
  matchType?: 'any-of' | 'all-of';
  tagColor?: string;
  theme?: ComponentProps<typeof FilterTag>['theme'];
}) {
  const highlightColor = theme === 'cyan' ? Colors.accentCyan() : undefined;
  const isAnyOf = matchType === 'any-of';
  const arr = useMemo(() => Array.from(state), [state]);
  const label = useMemo(() => {
    if (arr.length === 0) {
      return null;
    } else if (arr.length <= MAX_VALUES_TO_SHOW) {
      return (
        <>
          is&nbsp;{arr.length === 1 ? '' : <>{isAnyOf ? 'any of' : 'all of'}&nbsp;</>}
          {arr.map((value, index) => {
            return (
              <Fragment key={index}>
                <FilterTagHighlightedText
                  tooltipText={getTooltipText?.(value) ?? getStringValue?.(value)}
                  color={highlightColor}
                >
                  {getStringValue(value)}
                </FilterTagHighlightedText>
                {index < arr.length - 1 ? <>,&nbsp;</> : ''}
              </Fragment>
            );
          })}
        </>
      );
    } else {
      return (
        <Box flex={{direction: 'row', alignItems: 'center'}}>
          is <>{isAnyOf ? 'any of' : 'all of'}&nbsp;</>
          <Popover
            interactionKind="hover"
            position="bottom"
            content={
              <Box padding={{vertical: 8, horizontal: 12}} flex={{direction: 'column', gap: 4}}>
                {arr.map((value, index) => (
                  <div
                    key={index}
                    style={{
                      maxWidth: '500px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {renderLabel({value, isActive: true})}
                  </div>
                ))}
              </Box>
            }
          >
            <FilterTagHighlightedText
              color={highlightColor}
            >{`(${arr.length})`}</FilterTagHighlightedText>
          </Popover>
        </Box>
      );
    }
  }, [arr, getStringValue, getTooltipText, highlightColor, isAnyOf, renderLabel]);

  if (arr.length === 0) {
    return null;
  }
  return (
    <FilterTag
      iconName={icon}
      theme={theme}
      label={
        <Box flex={{direction: 'row', alignItems: 'center'}}>
          {capitalizeFirstLetter(name)}&nbsp;{label}
        </Box>
      }
      onRemove={onRemove}
    />
  );
}

export function capitalizeFirstLetter(string: string) {
  return string.charAt(0).toUpperCase() + string.slice(1).toLowerCase().replace(/_/g, ' ');
}

type SetFilterLabelProps = {
  value: any;
  isForcedActive?: boolean;
  filter: StaticSetFilter<any>;
  renderLabel: (value: any) => JSX.Element;
  allowMultipleSelections: boolean;
};
export function SetFilterLabel(props: SetFilterLabelProps) {
  const {value, filter, isForcedActive, renderLabel, allowMultipleSelections} = props;
  const isActive = filter.state.has(value);

  const labelRef = useRef<HTMLDivElement>(null);

  return (
    // 2px of margin to compensate for weird Checkbox CSS whose bounding box is smaller than the actual
    // SVG it contains with size="small"
    <Box
      flex={{direction: 'row', gap: 6, alignItems: 'center'}}
      ref={labelRef}
      margin={allowMultipleSelections ? {left: 2} : {}}
      style={{maxWidth: '500px'}}
    >
      {allowMultipleSelections ? (
        <Checkbox checked={isForcedActive || isActive} size="small" readOnly />
      ) : null}
      <Box
        flex={{direction: 'row', alignItems: 'center', grow: 1, shrink: 1}}
        style={{overflow: 'hidden'}}
      >
        <div style={{overflow: 'hidden'}}>{renderLabel({value, isActive})}</div>
      </Box>
    </Box>
  );
}
