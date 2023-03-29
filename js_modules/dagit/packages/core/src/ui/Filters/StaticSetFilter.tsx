import {Box, Checkbox, IconName, Popover} from '@dagster-io/ui';
import React from 'react';

import {Filter, FilterListenerCallback, FilterTag, FilterTagHighlightedText} from './Filter';

type SetFilterValue<T> = {
  value: T;
  match: string[];
};
export class StaticSetFilter<TValue> extends Filter<Set<TValue>, TValue> {
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

  getResults(query: string): {label: JSX.Element; key: string; value: TValue}[] {
    if (query === '') {
      return this.allValues.map(({value}) => ({
        label: <SetFilterLabel value={value} renderLabel={this.renderLabel} filter={this} />,
        key: this.getStringValue(value),
        value,
      }));
    }
    return this.allValues
      .filter(({match}) => match.some((value) => value.toLowerCase().includes(query.toLowerCase())))
      .map(({value}) => ({
        label: <SetFilterLabel value={value} renderLabel={this.renderLabel} filter={this} />,
        key: this.getStringValue(value),
        value,
      }));
  }

  onSelect({value}: {value: TValue}) {
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
    <Box
      flex={{direction: 'row', gap: 6, alignItems: 'center'}}
      ref={labelRef}
      margin={{left: 4}}
      style={{maxWidth: '500px'}}
    >
      <Checkbox
        checked={isActive}
        onChange={(_) => {
          labelRef.current?.click();
        }}
        size="small"
      />
      <Box
        flex={{direction: 'row', alignItems: 'center', grow: 1, shrink: 1}}
        style={{overflow: 'hidden'}}
      >
        <div style={{overflow: 'hidden'}}>{renderLabel({value, isActive})}</div>
      </Box>
    </Box>
  );
}
