import {render, getByText, fireEvent} from '@testing-library/react';
import React from 'react';

import {StaticSetFilter} from '../useStaticSetFilter';

const sampleValues = [
  {value: 'apple', match: ['apple', 'fruit']},
  {value: 'banana', match: ['banana', 'fruit']},
  {value: 'carrot', match: ['carrot', 'vegetable']},
  {value: 'potato', match: ['potato', 'vegetable']},
];

const renderLabel = ({value, isActive}: {value: any; isActive: boolean}) => (
  <span style={isActive ? {fontWeight: 'bold'} : {}}>{value}</span>
);

const getStringValue = (value: any) => value;

const filter = new StaticSetFilter({
  name: 'Food',
  icon: 'asset',
  allValues: sampleValues,
  renderLabel,
  getStringValue,
  initialState: new Set(),
});

describe('StaticSetFilter', () => {
  it('should be initially inactive', () => {
    expect(filter.isActive()).toBe(false);
  });

  it('should return all values when query is empty', () => {
    const results = filter.getResults('');
    expect(results.length).toBe(sampleValues.length);
  });

  it('should return filtered results based on query', () => {
    const results = filter.getResults('fruit');
    expect(results.length).toBe(2);
    expect(results.map((result) => result.value)).toEqual(['apple', 'banana']);
  });

  it('should update the filter state on onSelect', () => {
    expect(filter.getState().has('apple')).toBe(false);
    filter.onSelect({value: 'apple'});
    expect(filter.getState().has('apple')).toBe(true);
    filter.onSelect({value: 'apple'});
    expect(filter.getState().has('apple')).toBe(false);
  });

  it('should render SetFilterActiveState correctly', () => {
    const element = filter.renderActiveFilterState();
    const {getByText, queryByText, rerender} = render(element);

    // Initially, the filter is inactive
    expect(queryByText('Food is')).not.toBeInTheDocument();

    // Add a single value to the filter state
    filter.onSelect({value: 'apple'});
    rerender(<filter.renderActiveFilterState />);
    expect(getByText('Food is apple')).toBeInTheDocument();

    // Add multiple values to the filter state (total <= MAX_VALUES_TO_SHOW)
    filter.onSelect({value: 'banana'});
    rerender(<filter.renderActiveFilterState />);
    expect(getByText('Food is any of apple, banana')).toBeInTheDocument();

    // Add more values to the filter state (total > MAX_VALUES_TO_SHOW)
    filter.onSelect({value: 'carrot'});
    filter.onSelect({value: 'potato'});
    rerender(<filter.renderActiveFilterState />);
    const popoverTrigger = getByText('Food is any of 4 foods');
    expect(popoverTrigger).toBeInTheDocument();

    // Check if popover content is rendered correctly when hovering over the trigger
    fireEvent.mouseOver(popoverTrigger);
    const popoverContent = document.body.querySelector('.filter-dropdown')!;
    expect(popoverContent).toBeInTheDocument();
    expect(popoverContent.textContent).toContain('apple');
    expect(popoverContent.textContent).toContain('banana');
    expect(popoverContent.textContent).toContain('carrot');

    // Test the onRemove callback
    const removeButton = getByText('×');
    fireEvent.click(removeButton);
    expect(filter.isActive()).toBe(false);
  });
});
