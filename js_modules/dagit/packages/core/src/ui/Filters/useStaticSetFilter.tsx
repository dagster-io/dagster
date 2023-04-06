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
  getKey?: (value: TValue) => string;
  getStringValue: (value: TValue) => string;
  allValues: SetFilterValue<TValue>[];
  initialState?: Set<TValue> | TValue[];
  onStateChanged?: (state: Set<TValue>) => void;
};

export type StaticSetFilter<TValue> = FilterObject<Set<TValue>>;

export function useStaticSetFilter<TValue>({
  name,
  icon,
  getKey,
  allValues,
  renderLabel,
  initialState,
  getStringValue,
  onStateChanged,
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
      setState,
      isActive: state.size > 0,
      getResults: (query) => {
        if (query === '') {
          return allValues.map(({value}, index) => ({
            label: (
              <SetFilterLabel
                value={value}
                renderLabel={renderLabel}
                filter={filterObjRef.current}
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
              />
            ),
            key: getKey?.(value) || index.toString(),
            value,
          }));
      },
      onSelect: ({value}) => {
        const newState = new Set(filterObjRef.current.state);
        if (newState.has(value)) {
          newState.delete(value);
        } else {
          newState.add(value);
        }
        setState(newState);
      },

      activeJSX: (
        <SetFilterActiveState
          name={name}
          state={state}
          getStringValue={getStringValue}
          renderLabel={renderLabel}
          onRemove={() => {
            setState(new Set());
          }}
          icon={icon}
        />
      ),
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [name, icon, state, getStringValue, renderLabel, allValues],
  );
  const filterObjRef = useUpdatingRef(filterObj);
  return filterObj;
}

const MAX_VALUES_TO_SHOW = 3;

function SetFilterActiveState({
  name,
  state,
  icon,
  getStringValue,
  onRemove,
  renderLabel,
}: {
  name: string;
  icon: IconName;
  state: Set<any>;
  getStringValue: (value: any) => string;
  onRemove: () => void;
  renderLabel: (value: any) => JSX.Element;
}) {
  const arr = React.useMemo(() => Array.from(state), [state]);
  const label = React.useMemo(() => {
    if (arr.length === 0) {
      return null;
    } else if (arr.length <= MAX_VALUES_TO_SHOW) {
      return (
        <>
          is&nbsp;{arr.length === 1 ? '' : <>any of&nbsp;</>}
          {arr.map((value, index) => (
            <>
              <FilterTagHighlightedText>{getStringValue(value)}</FilterTagHighlightedText>
              {index < arr.length - 1 ? <>,&nbsp;</> : ''}
            </>
          ))}
        </>
      );
    } else {
      return (
        <Box flex={{direction: 'row', alignItems: 'center'}}>
          is any of&nbsp;
          <Popover
            interactionKind="hover"
            position="bottom"
            content={
              <Box padding={{vertical: 8, horizontal: 12}} flex={{direction: 'column', gap: 4}}>
                {arr.map((value) => (
                  <div
                    key={value}
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
  }, [arr, getStringValue, name, renderLabel]);

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

function capitalizeFirstLetter(string: string) {
  return string.charAt(0).toUpperCase() + string.slice(1);
}

type SetFilterLabelProps = {
  value: any;
  filter: StaticSetFilter<any>;
  renderLabel: (value: any) => JSX.Element;
};
function SetFilterLabel(props: SetFilterLabelProps) {
  const {value, filter, renderLabel} = props;
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
      <Checkbox checked={isActive} size="small" readOnly />
      <Box
        flex={{direction: 'row', alignItems: 'center', grow: 1, shrink: 1}}
        style={{overflow: 'hidden'}}
      >
        <div style={{overflow: 'hidden'}}>{renderLabel({value, isActive})}</div>
      </Box>
    </Box>
  );
}
