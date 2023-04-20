import {Box, IconName} from '@dagster-io/ui';
import React from 'react';

import {useUpdatingRef} from '../../hooks/useUpdatingRef';

import {FilterObject} from './useFilter';
import {SetFilterActiveState} from './useStaticSetFilter';

export type SuggestionFilterSuggestion<TValue> = {final?: boolean; value: TValue};

type Args<TValue> = {
  name: string;
  icon: IconName;

  state: TValue[]; // Active suggestions
  setState: (state: TValue[]) => void;
  initialSuggestions: SuggestionFilterSuggestion<TValue>[];

  onSuggestionClicked: (value: TValue) => Promise<SuggestionFilterSuggestion<TValue>[]> | void;
  getStringValue: (value: TValue) => string;
  getKey: (value: TValue) => string;
  renderLabel: ({value, isActive}: {value: TValue; isActive: boolean}) => JSX.Element;
  renderActiveStateLabel?: ({value, isActive}: {value: TValue; isActive: boolean}) => JSX.Element;
  isMatch: (value: TValue, query: string) => boolean;
  // Whether this is an OR or an AND of these filters. This will affect the wording "any of" vs "all of""
  matchType?: 'any-of' | 'all-of';
};

export type SuggestionFilter<TValue> = FilterObject & {
  state: TValue[];
};

export function useSuggestionFilter<TValue>({
  name,
  icon,
  state,
  setState,
  initialSuggestions,
  onSuggestionClicked,
  getStringValue,
  getKey,
  renderLabel,
  renderActiveStateLabel,
  isMatch,
  matchType = 'any-of',
}: Args<TValue>): SuggestionFilter<TValue> {
  const [nextSuggestionsLoading, setNextSuggestionsLoading] = React.useState(false);
  const [nextSuggestions, setNextSuggestions] = React.useState<
    SuggestionFilterSuggestion<TValue>[] | null
  >(null);
  const nextSuggestionsRef = useUpdatingRef(nextSuggestions);
  const nextSuggestionsLoadingRef = useUpdatingRef(nextSuggestionsLoading);

  const filterObj: SuggestionFilter<TValue> = React.useMemo(
    () => ({
      name,
      icon,
      state,
      isActive: state.length > 0,
      onUnselected: () => {
        setNextSuggestions(null);
        setNextSuggestionsLoading(false);
      },
      isLoadingFilters: nextSuggestionsLoading,
      getResults: (query: string) => {
        if (nextSuggestionsRef.current || nextSuggestionsLoadingRef.current) {
          return (
            nextSuggestionsRef.current
              ?.filter(({value}) => query === '' || isMatch(value, query))
              .map((value, index) => ({
                label: (
                  <SuggestionFilterLabel
                    value={value.value}
                    renderLabel={renderLabel}
                    filter={filterObjRef.current}
                  />
                ),
                key: getKey?.(value.value) || index.toString(),
                value,
              })) || []
          );
        }
        return initialSuggestions
          .filter(({value}) => query === '' || isMatch(value, query))
          .map((value, index) => ({
            label: (
              <SuggestionFilterLabel
                value={value.value}
                renderLabel={renderLabel}
                filter={filterObjRef.current}
              />
            ),
            key: getKey?.(value.value) || index.toString(),
            value,
          }));
      },

      onSelect: async ({value}) => {
        if (value.final) {
          if (state.includes(value.value)) {
            setState(state.filter((v) => v !== value.value));
          } else {
            setState([...state, value.value]);
          }
        } else {
          const result = onSuggestionClicked(value.value);
          if (result) {
            setNextSuggestionsLoading(true);
            const nextSuggestions = await result;
            setNextSuggestions(nextSuggestions);
            setNextSuggestionsLoading(false);
          }
        }
      },

      activeJSX: (
        <SetFilterActiveState
          name={name}
          state={new Set(state)}
          getStringValue={getStringValue}
          renderLabel={renderActiveStateLabel || renderLabel}
          onRemove={() => {
            setState([]);
          }}
          icon={icon}
          matchType={matchType}
        />
      ),
    }),
    // Missing filterObjRef because it's a ref
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [
      name,
      icon,
      state,
      getStringValue,
      renderLabel,
      renderActiveStateLabel,
      nextSuggestions,
      nextSuggestionsLoading,
      initialSuggestions,
      getKey,
      isMatch,
      setState,
      onSuggestionClicked,
      matchType,
    ],
  );
  const filterObjRef = useUpdatingRef(filterObj);
  return filterObj;
}

export function capitalizeFirstLetter(string: string) {
  return string.charAt(0).toUpperCase() + string.slice(1);
}

type SuggestionFilterLabelProps = {
  value: any;
  filter: SuggestionFilter<any>;
  renderLabel: (value: any) => JSX.Element;
};
function SuggestionFilterLabel(props: SuggestionFilterLabelProps) {
  const {value, filter, renderLabel} = props;
  const isActive = filter.state.includes(value);

  const labelRef = React.useRef<HTMLDivElement>(null);

  return (
    // 4 px of margin to compensate for weird Checkbox CSS whose bounding box is smaller than the actual
    // SVG it contains with size="small"
    <Box
      flex={{direction: 'row', gap: 6, alignItems: 'center'}}
      ref={labelRef}
      margin={{left: 4}}
      style={{maxWidth: '500px', overflow: 'hidden'}}
    >
      <div style={{overflow: 'hidden'}}>{renderLabel({value, isActive})}</div>
    </Box>
  );
}
