import {render, fireEvent, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';

import '@testing-library/jest-dom/extend-expect';
import {FilterDropdown, FilterDropdownButton} from '../FilterDropdown';
import {FilterObject} from '../useFilter';

let mockFilters: FilterObject[];
beforeEach(() => {
  mockFilters = [
    {
      name: 'Type',
      icon: 'asset',
      onSelect: jest.fn(),
      getResults: jest.fn((key) =>
        key === 'nonexistent'
          ? []
          : [
              {label: 'Type 1', key: 'type1', value: 1},
              {label: 'Type 2', key: 'type2', value: 2},
            ],
      ),
    },
    {
      name: 'Status',
      icon: 'asset',
      onSelect: jest.fn(),
      getResults: jest.fn((key) =>
        key === 'nonexistent'
          ? []
          : [
              {label: <>Active</>, key: 'active', value: 'active'},
              {label: <>Inactive</>, key: 'inactive', value: 'inactive'},
            ],
      ),
    },
  ] as any;
});

describe('FilterDropdown', () => {
  test('displays filter categories initially', () => {
    render(
      <FilterDropdown
        filters={mockFilters}
        setIsOpen={jest.fn()}
        setPortaledElements={jest.fn()}
      />,
    );
    expect(screen.getByText(/Type/g)).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
  });

  test('searches and displays matching filters', async () => {
    render(
      <FilterDropdown
        filters={mockFilters}
        setIsOpen={jest.fn()}
        setPortaledElements={jest.fn()}
      />,
    );
    const searchInput = screen.getByPlaceholderText('Search filters...');
    fireEvent.change(searchInput, {target: {value: 'type'}});
    await waitFor(() => expect(screen.getByText('Type 1')).toBeInTheDocument());
    await waitFor(() => expect(screen.getByText('Type 2')).toBeInTheDocument());
    await waitFor(() => expect(mockFilters[0].getResults).toHaveBeenCalledWith('type'));
    await waitFor(() => expect(mockFilters[1].getResults).toHaveBeenCalledWith('type'));
  });

  test('displays no results when no filters match', async () => {
    render(
      <FilterDropdown
        filters={mockFilters}
        setIsOpen={jest.fn()}
        setPortaledElements={jest.fn()}
      />,
    );
    const searchInput = screen.getByPlaceholderText('Search filters...');
    fireEvent.change(searchInput, {target: {value: 'nonexistent'}});
    await waitFor(() => expect(screen.getByText('No results')).toBeInTheDocument());
  });
});

describe('FilterDropdownButton', () => {
  test('opens and closes the dropdown on click', async () => {
    render(<FilterDropdownButton filters={mockFilters} />);
    const button = screen.getByRole('button');
    await userEvent.click(button);
    await waitFor(() => {
      expect(screen.getByText(/Type/g)).toBeInTheDocument();
    });
    await userEvent.click(button);
    await waitFor(() => {
      expect(screen.queryByText(/Type/g)).not.toBeInTheDocument();
    });
  });

  test('closes the dropdown when clicking outside', async () => {
    render(<FilterDropdownButton filters={mockFilters} />);
    const button = screen.getByRole('button');
    await userEvent.click(button);
    await waitFor(() => {
      expect(screen.getByText(/Type/g)).toBeInTheDocument();
    });
    await userEvent.click(document.body);
    await waitFor(() => {
      expect(screen.queryByText(/Type/g)).not.toBeInTheDocument();
    });
  });
});

describe('FilterDropdown Accessibility', () => {
  const testKeyboardNavigation = async (nextKey: any, prevKey: any, enterKey: any) => {
    render(<FilterDropdownButton filters={mockFilters} />);

    await userEvent.click(screen.getByRole('button'));
    expect(screen.getByRole('menu')).toBeInTheDocument();

    const input = screen.getByLabelText('Search filters');
    expect(input).toHaveFocus();

    fireEvent.keyDown(document.activeElement!, nextKey);
    await waitFor(() => {
      expect(screen.getByText('Type').closest('a')).toHaveClass('bp4-active');
    });

    fireEvent.keyDown(document.activeElement!, nextKey);
    await waitFor(() => {
      expect(screen.getByText('Status').closest('a')).toHaveClass('bp4-active');
    });

    fireEvent.keyDown(document.activeElement!, prevKey);
    await waitFor(() => {
      expect(screen.getByText('Type').closest('a')).toHaveClass('bp4-active');
    });

    fireEvent.keyDown(document.activeElement!, nextKey);
    await waitFor(() => {
      expect(screen.getByText('Status').closest('a')).toHaveClass('bp4-active');
    });

    fireEvent.keyDown(document.activeElement!, nextKey);
    expect(input).toHaveFocus();

    fireEvent.keyDown(document.activeElement!, nextKey);
    await waitFor(() => {
      expect(screen.getByText('Type').closest('a')).toHaveClass('bp4-active');
    });

    fireEvent.keyDown(document.activeElement!, nextKey);
    await waitFor(() => {
      expect(screen.getByText('Status').closest('a')).toHaveClass('bp4-active');
    });

    fireEvent.keyDown(document.activeElement!, enterKey);

    await waitFor(() => {
      expect(input).toHaveFocus();
    });

    fireEvent.keyDown(document.activeElement!, nextKey);
    fireEvent.keyDown(document.activeElement!, nextKey);

    expect(screen.getByText('Inactive').closest('a')).toHaveClass('bp4-active');
    fireEvent.keyDown(document.activeElement!, enterKey);

    await waitFor(() => {
      expect(mockFilters[1].onSelect).toHaveBeenCalled();
    });
  };

  // eslint-disable-next-line jest/expect-expect
  test('keyboard navigation and selection with arrow keys', async () => {
    await testKeyboardNavigation(
      {key: 'ArrowDown', code: 'ArrowDown'},
      {key: 'ArrowUp', code: 'ArrowUp'},
      {key: 'Enter', code: 'Enter'},
    );
  });

  // eslint-disable-next-line jest/expect-expect
  test('keyboard navigation and selection with Tab and Shift+Tab keys', async () => {
    await testKeyboardNavigation(
      {key: 'Tab', code: 'Tab'},
      {key: 'Tab', code: 'Tab', shiftKey: true},
      {key: ' ', code: ' '},
    );
  });

  test('escape key behavior', async () => {
    render(<FilterDropdownButton filters={mockFilters} />);

    await userEvent.click(screen.getByRole('button'));
    expect(screen.getByRole('menu')).toBeVisible();

    const input = screen.getByLabelText('Search filters');
    expect(input).toHaveFocus();

    expect(screen.queryByText('Type 1')).toBeNull();

    fireEvent.keyDown(document.activeElement!, {key: 'ArrowDown', code: 'ArrowDown'});

    fireEvent.keyDown(document.activeElement!, {key: 'Enter', code: 'Enter'});

    await waitFor(() => {
      expect(screen.getByText('Type 1')).toBeVisible();
    });

    fireEvent.keyDown(document.activeElement!, {key: 'Escape', code: 'Escape'});

    expect(screen.queryByText('Type 1')).toBeNull();

    fireEvent.keyDown(document.activeElement!, {key: 'Escape', code: 'Escape'});
    await waitFor(() => {
      expect(screen.queryByRole('menu')).not.toBeInTheDocument();
    });
  });
});
