import {BaseTag, Colors, Icon, IconName} from '@dagster-io/ui';
import React from 'react';
import styled from 'styled-components/macro';

export type FilterListenerCallback<TState> = (value: {
  state: TState;
  previousActive: boolean;
  active: boolean;
}) => void;

export abstract class Filter<TState, TValue> {
  private listeners: FilterListenerCallback<TState>[];

  constructor(public readonly name: string, public readonly icon: IconName, private state: TState) {
    this.name = name;
    this.icon = icon;
    this.state = state;
    this.listeners = [];
  }

  public abstract isActive(): boolean;

  public abstract renderActiveFilterState(): JSX.Element | null;
  public abstract getResults(query: string): {label: JSX.Element; value: TValue}[];

  public abstract onSelect(
    value: TValue,
    close: () => void,
    createPortal: (element: JSX.Element) => () => void,
  ): void;

  public setState(state: TState) {
    const previousActive = this.isActive();
    this.state = state;
    this.listeners.forEach((l) =>
      l({
        state,
        previousActive,
        active: this.isActive(),
      }),
    );
  }
  public getState(): TState {
    return this.state;
  }

  public subscribe(callback: FilterListenerCallback<TState>): () => void {
    this.listeners.push(callback);
    return () => {
      this.listeners = this.listeners.filter((l) => l !== callback);
    };
  }
}

export const FilterTag = ({
  iconName,
  label,
  onRemove,
}: {
  label: JSX.Element;
  iconName: IconName;
  onRemove: () => void;
}) => (
  <BaseTag
    icon={<Icon name={iconName} color={Colors.Link} />}
    rightIcon={
      <div onClick={onRemove} style={{cursor: 'pointer'}}>
        <Icon name="close" color={Colors.Link} />
      </div>
    }
    label={label}
    fillColor={Colors.Blue50}
    textColor={Colors.Link}
  />
);

export const FilterTagHighlightedText = styled.span`
  color: ${Colors.Blue500};
  font-weight: 600;
  font-size: 12px;
`;
