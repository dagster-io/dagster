import {Box, Checkbox, IconName, Popover} from '@dagster-io/ui';
import React from 'react';

import {Filter, FilterListenerCallback, FilterTag, FilterTagHighlightedText} from './Filter';

type SetFilterValue<T> = {
  value: T;
  match: string[];
};
export class SetFilter<TValue> extends Filter<Set<TValue>, TValue> {
  public readonly allValues: SetFilterValue<TValue>[];
  private readonly renderLabel: (props: {value: TValue; isActive: boolean}) => JSX.Element;
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
    renderLabel: (props: {value: TValue; isActive: boolean}) => JSX.Element;
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
        label: <SetFilterLabel value={value} renderLabel={this.renderLabel} filter={this} />,
        value,
      }));
    }
    return this.allValues
      .filter(({match}) => match.some((value) => value.toLowerCase().includes(query.toLowerCase())))
      .map(({value}) => ({
        label: <SetFilterLabel value={value} renderLabel={this.renderLabel} filter={this} />,
        value,
      }));
  }

  onSelect(value: TValue, _: (isOpen: boolean) => void): JSX.Element | null {
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
            position="bottom"
            content={
              <Box
                padding={{vertical: 8, horizontal: 12}}
                flex={{direction: 'column', gap: 4}}
                style={{maxHeight: '300px', overflow: 'auto'}}
              >
                {arr.map((value) => (
                  <div key={value}>{renderLabel({value, isActive: true})}</div>
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
  }, [arr, getStringValue, name, renderLabel]);

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

type SetFilterLabelProps = {
  value: any;
  filter: SetFilter<any>;
  renderLabel: (value: any) => JSX.Element;
};
function SetFilterLabel(props: SetFilterLabelProps) {
  const {value, filter, renderLabel} = props;
  const [isActive, setIsActive] = React.useState(filter.getState().has(value));
  React.useEffect(() => {
    const listener: FilterListenerCallback<any> = () => {
      setIsActive(filter.getState().has(value));
    };
    return filter.subscribe(listener);
  }, [filter, value]);

  const labelRef = React.useRef<HTMLDivElement>(null);

  return (
    // 4 px of margin to compensate for weird Checkbox CSS whose bounding box is smaller than the actual
    // SVG it contains with size="small"
    <Box flex={{direction: 'row', gap: 6}} ref={labelRef} margin={{left: 4}}>
      <Checkbox
        checked={isActive}
        onChange={(_) => {
          labelRef.current?.click();
        }}
        size="small"
      />
      {renderLabel({value, isActive})}
    </Box>
  );
}
