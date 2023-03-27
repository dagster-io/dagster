import {Box, IconName, Popover, Tooltip} from '@dagster-io/ui';
import {Filter, FilterTag, FilterTagHighlightedText} from './Filter';
import React from 'react';

type SetFilterValue<T> = {
  value: T;
  match: string[];
};
export class SetFilter<TValue> extends Filter<Set<TValue>, TValue> {
  public readonly allValues: SetFilterValue<TValue>[];
  private readonly renderLabel: (value: TValue) => JSX.Element;
  private readonly getStringValue: (value: TValue) => string;

  constructor({
    name,
    icon,
    allValues,
    renderLabel,
    initialState,
    getStringValue,
  }: {
    name: string;
    icon: IconName;
    renderLabel: (value: TValue) => JSX.Element;
    getStringValue: (value: TValue) => string;
    allValues: SetFilterValue<TValue>[];
    initialState?: Set<TValue> | TValue[];
  }) {
    super(name, icon, new Set(initialState || []));
    this.allValues = allValues;
    this.renderLabel = renderLabel;
    this.getStringValue = getStringValue;
  }
  renderActiveFilterState() {
    return (
      <SetFilterActiveState
        name={this.name}
        state={this.getState()}
        getStringValue={this.getStringValue}
        renderLabel={this.renderLabel}
        onRemove={() => {
          this.setState(new Set());
        }}
        icon={this.icon}
      />
    );
  }

  isActive(): boolean {
    return this.getState().size > 0;
  }

  getResults(query: string): {label: JSX.Element; value: TValue}[] {
    if (query === '') {
      return this.allValues.map(({value}) => ({
        label: this.renderLabel(value),
        value,
      }));
    }
    return this.allValues
      .filter(({match}) => match.some((value) => value.toLowerCase().includes(query.toLowerCase())))
      .map(({value}) => ({
        label: this.renderLabel(value),
        value,
      }));
  }

  onSelect(value: TValue): JSX.Element | null {
    if (this.getState().has(value)) {
      const nextState = new Set(this.getState());
      nextState.delete(value);
      this.setState(nextState);
    } else {
      this.setState(new Set(this.getState()).add(value));
    }
    return null;
  }
}

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
    } else if (arr.length <= 3) {
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
    } else if (arr.length > 3) {
      return (
        <div>
          is any of{' '}
          <Popover
            interactionKind="hover"
            content={
              <Box
                padding={{vertical: 8, horizontal: 12}}
                flex={{direction: 'column', gap: 4}}
                style={{maxHeight: '300px', overflow: 'auto'}}
              >
                {arr.map((value) => (
                  <div>{renderLabel(value)}</div>
                ))}
              </Box>
            }
          >
            <FilterTagHighlightedText>
              {arr.length} {name.toLowerCase()}s
            </FilterTagHighlightedText>
          </Popover>
        </div>
      );
    }
    return null;
  }, [arr]);
  if (arr.length === 0) {
    return null;
  }
  return (
    <FilterTag
      iconName={icon}
      label={
        <Box flex={{direction: 'row'}}>
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
