import {Box, Checkbox, IconName, Popover} from '@dagster-io/ui';
import React from 'react';

import {useUpdatingRef} from '../../hooks/useUpdatingRef';

import {FilterObject, FilterTag, FilterTagHighlightedText} from './useFilter';

type SetFilterValue<T> = {
  value: T;
  match: string[];
};
type Args<TValue> = {
  name: string;
  icon: IconName;
  renderLabel: (props: {value: TValue; isActive: boolean}) => JSX.Element;
  renderActiveStateLabel?: (props: {value: TValue; isActive: boolean}) => JSX.Element;
  getKey?: (value: TValue) => string;
  getStringValue: (value: TValue) => string;
  allValues: SetFilterValue<TValue>[];
  initialState?: Set<TValue> | TValue[];
  onStateChanged?: (state: Set<TValue>) => void;
  allowMultipleSelections?: boolean;
  matchType?: 'any-of' | 'all-of';
};

export type StaticSetFilter<TValue> = FilterObject & {
  state: Set<TValue>;
  setState: (state: Set<TValue>) => void;
};

export function useStaticSetFilter<TValue>({
  name,
  icon,
  getKey,
  allValues,
  renderLabel,
  renderActiveStateLabel,
  initialState,
  getStringValue,
  onStateChanged,
  allowMultipleSelections = true,
  matchType = 'any-of',
}: Args<TValue>): StaticSetFilter<TValue> {
  const [state, setState] = React.useState(new Set(initialState || []));

  React.useEffect(() => {
    onStateChanged?.(state);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state]);

  React.useEffect(() => {
    setState(initialState ? new Set(initialState) : new Set());
  }, [initialState]);

  const filterObj: StaticSetFilter<TValue> = React.useMemo(
    () => ({
      name,
      icon,
      state,
      isActive: state.size > 0,
      getResults: (query) => {
        if (query === '') {
          return allValues.map(({value}, index) => ({
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
        return allValues
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
      },
      onSelect: ({value}) => {
        let newState = new Set(filterObjRef.current.state);
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
      },

      activeJSX: (
        <SetFilterActiveState
          name={name}
          state={state}
          getStringValue={getStringValue}
          renderLabel={renderActiveStateLabel || renderLabel}
          onRemove={() => {
            setState(new Set());
          }}
          icon={icon}
          matchType={matchType}
        />
      ),
      setState,
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [name, icon, state, getStringValue, renderLabel, allValues, matchType, renderActiveStateLabel],
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
  matchType,
}: {
  name: string;
  icon: IconName;
  state: Set<any>;
  getStringValue: (value: any) => string;
  onRemove: () => void;
  renderLabel: (value: any) => JSX.Element;
  matchType: 'any-of' | 'all-of';
}) {
  const isAnyOf = matchType === 'any-of';
  const arr = React.useMemo(() => Array.from(state), [state]);
  const label = React.useMemo(() => {
    if (arr.length === 0) {
      return null;
    } else if (arr.length <= MAX_VALUES_TO_SHOW) {
      return (
        <>
          is&nbsp;{arr.length === 1 ? '' : <>{isAnyOf ? 'any of' : 'all of'}&nbsp;</>}
          {arr.map((value, index) => (
            <React.Fragment key={index}>
              <FilterTagHighlightedText>{getStringValue(value)}</FilterTagHighlightedText>
              {index < arr.length - 1 ? <>,&nbsp;</> : ''}
            </React.Fragment>
          ))}
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
                {arr.map((value) => (
                  <div
                    key={getStringValue(value)}
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
            <FilterTagHighlightedText>{`${
              arr.length
            } ${name.toLowerCase()}s`}</FilterTagHighlightedText>
          </Popover>
        </Box>
      );
    }
  }, [arr, getStringValue, isAnyOf, name, renderLabel]);

  if (arr.length === 0) {
    return null;
  }
  return (
    <FilterTag
      iconName={icon}
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
  filter: StaticSetFilter<any>;
  renderLabel: (value: any) => JSX.Element;
  allowMultipleSelections: boolean;
};
export function SetFilterLabel(props: SetFilterLabelProps) {
  const {value, filter, renderLabel, allowMultipleSelections} = props;
  const isActive = filter.state.has(value);

  const labelRef = React.useRef<HTMLDivElement>(null);

  return (
    // 4 px of margin to compensate for weird Checkbox CSS whose bounding box is smaller than the actual
    // SVG it contains with size="small"
    <Box
      flex={{direction: 'row', gap: 6, alignItems: 'center'}}
      ref={labelRef}
      margin={{left: 4}}
      style={{maxWidth: '500px'}}
    >
      {allowMultipleSelections ? <Checkbox checked={isActive} size="small" readOnly /> : null}
      <Box
        flex={{direction: 'row', alignItems: 'center', grow: 1, shrink: 1}}
        style={{overflow: 'hidden'}}
      >
        <div style={{overflow: 'hidden'}}>{renderLabel({value, isActive})}</div>
      </Box>
    </Box>
  );
}
