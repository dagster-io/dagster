import {Box, IconName} from '@dagster-io/ui-components';
import {useMemo, useRef, useState} from 'react';

import {FilterObject} from './useFilter';
import {SetFilterActiveState} from './useStaticSetFilter';
import {useUpdatingRef} from '../../hooks/useUpdatingRef';

export type SuggestionFilterSuggestion<TValue> = {final?: boolean; value: TValue};

type Args<TValue> = {
  name: string;
  icon: IconName;

  // Allows creating a custom search result from the query
  freeformSearchResult?: (
    query: string,
    suggestionPath: TValue[],
  ) => SuggestionFilterSuggestion<TValue> | SuggestionFilterSuggestion<TValue>[] | null;
  freeformResultPosition?: 'start' | 'end';

  state: TValue[]; // Active suggestions
  setState: (state: TValue[]) => void;

  allowMultipleSelections?: boolean;
  initialSuggestions: SuggestionFilterSuggestion<TValue>[];
  getNoSuggestionsPlaceholder?: (query: string) => string;
  onSuggestionClicked: (value: TValue) => Promise<SuggestionFilterSuggestion<TValue>[]> | void;

  getStringValue: (value: TValue) => string;
  getTooltipText?: (value: TValue) => string;
  getKey: (value: TValue) => string;
  renderLabel: ({value, isActive}: {value: TValue; isActive: boolean}) => JSX.Element;
  renderActiveStateLabel?: ({value, isActive}: {value: TValue; isActive: boolean}) => JSX.Element;
  isMatch: (value: TValue, query: string) => boolean;
  // Whether this is an OR or an AND of these filters. This will affect the wording "any of" vs "all of""
  matchType?: 'any-of' | 'all-of';
};

export type SuggestionFilter<TValue> = FilterObject<SuggestionFilterSuggestion<TValue>> & {
  state: TValue[];
};

export function useSuggestionFilter<TValue>({
  name,
  icon,
  freeformSearchResult,
  state,
  setState,
  initialSuggestions,
  allowMultipleSelections = true,
  freeformResultPosition = 'start',
  onSuggestionClicked,
  getNoSuggestionsPlaceholder,
  getStringValue,
  getKey,
  renderLabel,
  renderActiveStateLabel,
  isMatch,
  matchType = 'any-of',
  getTooltipText,
}: Args<TValue>): SuggestionFilter<TValue> {
  const [nextSuggestionsLoading, setNextSuggestionsLoading] = useState(false);
  const [nextSuggestions, setNextSuggestions] = useState<
    SuggestionFilterSuggestion<TValue>[] | null
  >(null);
  const nextSuggestionsRef = useUpdatingRef(nextSuggestions);
  const nextSuggestionsLoadingRef = useUpdatingRef(nextSuggestionsLoading);
  const [suggestionPath, setSuggestionPath] = useState<TValue[]>([]);

  const filterObj: SuggestionFilter<TValue> = useMemo(
    () => ({
      name,
      icon,
      state,
      isActive: state.length > 0,
      onUnselected: () => {
        setNextSuggestions(null);
        setNextSuggestionsLoading(false);
        setSuggestionPath([]);
      },
      isLoadingFilters: nextSuggestionsLoading,
      getNoResultsPlaceholder: getNoSuggestionsPlaceholder,
      getResults: (query: string) => {
        let results;
        let hasExactMatch = false;
        if (nextSuggestionsRef.current || nextSuggestionsLoadingRef.current) {
          results =
            nextSuggestionsRef.current
              ?.filter(({value}) => {
                if (getStringValue(value) === query) {
                  hasExactMatch = true;
                }
                return query === '' || isMatch(value, query);
              })
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
              })) || [];
        } else {
          results = initialSuggestions
            .filter(({value}) => {
              if (getStringValue(value) === query) {
                hasExactMatch = true;
              }
              return query === '' || isMatch(value, query);
            })
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
        }
        if (!hasExactMatch && freeformSearchResult && query.length) {
          const suggestion = freeformSearchResult(query, suggestionPath);
          if (suggestion) {
            const suggestions = Array.isArray(suggestion) ? suggestion : [suggestion];
            const freeformResults =
              suggestions
                .filter((s): s is SuggestionFilterSuggestion<TValue> => s !== null)
                .map((suggestion) => ({
                  label: (
                    <SuggestionFilterLabel
                      value={suggestion.value}
                      renderLabel={renderLabel}
                      filter={filterObjRef.current}
                    />
                  ),
                  key: getKey?.(suggestion.value) || 'freeform',
                  value: suggestion,
                })) || [];

            if (freeformResultPosition === 'start') {
              results.unshift(...freeformResults);
            } else {
              results.push(...freeformResults);
            }
          }
        }
        return results;
      },

      onSelect: async ({value, clearSearch}) => {
        if (value.final) {
          if (!allowMultipleSelections) {
            const result = state.includes(value.value) ? [] : [value.value];
            setState(result);
          } else {
            const result = state.includes(value.value)
              ? state.filter((v) => v !== value.value)
              : [...state, value.value];
            setState(result);
          }
        } else {
          clearSearch();
          const result = onSuggestionClicked(value.value);
          setSuggestionPath((path) => [...path, value.value]);
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
          getTooltipText={getTooltipText}
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
      nextSuggestionsLoading,
      getStringValue,
      getNoSuggestionsPlaceholder,
      renderActiveStateLabel,
      renderLabel,
      matchType,
      nextSuggestionsRef,
      nextSuggestionsLoadingRef,
      initialSuggestions,
      freeformSearchResult,
      isMatch,
      getKey,
      suggestionPath,
      setState,
      onSuggestionClicked,
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

  const labelRef = useRef<HTMLDivElement>(null);

  return (
    // 2px of margin to compensate for weird Checkbox CSS whose bounding box is smaller than the actual
    // SVG it contains with size="small"
    <Box
      flex={{direction: 'row', gap: 6, alignItems: 'center'}}
      ref={labelRef}
      margin={{left: 2}}
      style={{maxWidth: '500px', overflow: 'hidden'}}
    >
      <div style={{overflow: 'hidden'}}>{renderLabel({value, isActive})}</div>
    </Box>
  );
}
