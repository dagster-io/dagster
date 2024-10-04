import {Box, Checkbox, Colors, IconName, Popover} from '@dagster-io/ui-components';
import {ComponentProps, Fragment, useMemo, useRef} from 'react';
import {useStaticSetFilterSorter} from 'shared/ui/BaseFilters/useStaticSetFilterSorter.oss';

import {FilterObject, FilterTag, FilterTagHighlightedText} from './useFilter';
import {useUpdatingRef} from '../../hooks/useUpdatingRef';

export type SetFilterValue<T> = {
  value: T;
  match: string[];
};

export type StaticBaseConfig<TValue> = {
  // Label that shows up in the filter menu
  name: string;
  // Label that shows up in the active filters bar.
  filterBarTagLabel?: JSX.Element;
  icon: IconName;
  renderLabel: (props: {value: TValue; isActive: boolean}) => JSX.Element;
  renderActiveStateLabel?: (props: {value: TValue; isActive: boolean}) => JSX.Element;
  getKey?: (value: TValue) => string;
  getStringValue: (value: TValue) => string;
  getTooltipText?: (value: TValue) => string;
  matchType?: 'any-of' | 'all-of';
  isLoadingFilters?: boolean;
};

type FilterArgs<TValue> = StaticBaseConfig<TValue> & {
  allValues: SetFilterValue<TValue>[];

  state: Set<TValue> | TValue[];
  onStateChanged: (state: Set<TValue>) => void;

  allowMultipleSelections?: boolean;
  selectAllText?: React.ReactNode;
  canSelectAll?: boolean;
  menuWidth?: number | string;
  closeOnSelect?: boolean;
  isLoadingFilters?: boolean;
};

export type StaticSetFilter<TValue> = FilterObject & {
  state: Set<TValue>;
  setState: (state: Set<TValue>) => void;
  selectAll: () => void;
};

const selectAllSymbol = Symbol.for('useStaticSetFilter:SelectAll');

export function useStaticSetFilter<TValue>({
  name,
  icon,
  getKey,
  allValues: _unsortedValues,
  renderLabel,
  renderActiveStateLabel,
  filterBarTagLabel,
  isLoadingFilters,
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
  const sortConfig = useStaticSetFilterSorter();

  const allValues = useMemo(() => {
    const sorter = sortConfig?.[name];
    if (sorter) {
      return _unsortedValues.sort(sorter);
    }
    return _unsortedValues;
  }, [sortConfig, name, _unsortedValues]);

  const currentQueryRef = useRef<string>('');

  const stateAsSet = useMemo(() => {
    if (state instanceof Set) {
      return state;
    }
    return new Set(state);
  }, [state]);

  const filterObj: StaticSetFilter<TValue> = useMemo(
    () => ({
      name,
      icon,
      state: stateAsSet,
      isActive: stateAsSet.size > 0,
      isLoadingFilters,
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
                  isForcedActive={stateAsSet.size === allValues.length}
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
            onStateChanged(
              new Set([...Array.from(state), ...selectResults.map(({value}) => value)]),
            );
          } else {
            const stateCopy = new Set(state);
            selectResults.forEach(({value}) => {
              stateCopy.delete(value);
            });
            onStateChanged(stateCopy);
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
        onStateChanged(newState);
        if (closeOnSelect) {
          close();
        }
      },
      selectAll() {
        this.onSelect({
          value: selectAllSymbol,
          close: () => {},
          createPortal: () => () => {},
          clearSearch: () => {},
        });
      },

      activeJSX: (
        <SetFilterActiveState
          name={name}
          state={stateAsSet}
          getStringValue={getStringValue}
          getTooltipText={getTooltipText}
          renderLabel={renderActiveStateLabel || renderLabel}
          onRemove={() => {
            onStateChanged(new Set());
          }}
          icon={icon}
          matchType={matchType}
          filterBarTagLabel={filterBarTagLabel}
        />
      ),
      setState: (val) => onStateChanged(val),
      menuWidth,
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [
      name,
      icon,
      stateAsSet,
      getStringValue,
      renderActiveStateLabel,
      renderLabel,
      matchType,
      allValues,
      allowMultipleSelections,
      getKey,
      selectAllText,
      isLoadingFilters,
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
  filterBarTagLabel,
}: {
  name: string;
  filterBarTagLabel?: JSX.Element;
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
  const startingMessage = useMemo(() => {
    return (
      <>
        {filterBarTagLabel ?? (
          <>
            {capitalizeFirstLetter(name)} is {arr.length === 1 ? '' : isAnyOf ? 'any of' : 'all of'}
          </>
        )}
        &nbsp;
      </>
    );
  }, [arr.length, filterBarTagLabel, isAnyOf, name]);
  const label = useMemo(() => {
    if (arr.length === 0) {
      return null;
    } else if (arr.length <= MAX_VALUES_TO_SHOW) {
      return (
        <>
          {startingMessage}
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
          {startingMessage}
          <Popover
            interactionKind="hover"
            position="bottom"
            content={
              <Box
                padding={{vertical: 8, horizontal: 12}}
                style={{
                  maxHeight: 'min(500px, 50vh)',
                  overflowY: 'scroll',
                  display: 'grid',
                  gap: 4,
                }}
              >
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
  }, [arr, getStringValue, getTooltipText, highlightColor, renderLabel, startingMessage]);

  if (arr.length === 0) {
    return null;
  }
  return (
    <FilterTag
      iconName={icon}
      theme={theme}
      label={<Box flex={{direction: 'row', alignItems: 'center'}}>{label}</Box>}
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
