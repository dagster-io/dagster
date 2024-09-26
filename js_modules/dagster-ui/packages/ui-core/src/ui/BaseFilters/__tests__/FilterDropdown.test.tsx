import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import {mockViewportClientRect, restoreViewportClientRect} from '../../../testing/mocking';
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

beforeAll(() => {
  mockViewportClientRect();
});

afterAll(() => {
  restoreViewportClientRect();
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
    expect(screen.getByText(/type/i)).toBeInTheDocument();
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
    await userEvent.type(searchInput, 'type');
    await waitFor(() => expect(screen.getByText('Type 1')).toBeInTheDocument());
    await waitFor(() => expect(screen.getByText('Type 2')).toBeInTheDocument());
    await waitFor(() => expect(mockFilters[0]!.getResults).toHaveBeenCalledWith('type'));
    await waitFor(() => expect(mockFilters[1]!.getResults).toHaveBeenCalledWith('type'));
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
    await userEvent.type(searchInput, 'nonexistent');
    await waitFor(() => expect(screen.getByText('No results')).toBeInTheDocument());
  });
});

describe('FilterDropdownButton', () => {
  test('opens and closes the dropdown on click', async () => {
    render(<FilterDropdownButton filters={mockFilters} />);
    const button = screen.getByRole('button');
    await userEvent.click(button);
    await waitFor(() => {
      expect(screen.getByText(/type/i)).toBeInTheDocument();
    });
    await userEvent.click(button);
    await waitFor(() => {
      expect(screen.queryByText(/type/i)).not.toBeInTheDocument();
    });
  });

  test('closes the dropdown when clicking outside', async () => {
    render(<FilterDropdownButton filters={mockFilters} />);
    const button = screen.getByRole('button');
    await userEvent.click(button);
    await waitFor(() => {
      expect(screen.getByText(/type/i)).toBeInTheDocument();
    });
    await userEvent.click(document.body);
    await waitFor(() => {
      expect(screen.queryByText(/type/i)).not.toBeInTheDocument();
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

    await userEvent.keyboard(nextKey);
    await waitFor(() => {
      expect(screen.getByText('Type').closest('a')).toHaveClass('bp5-active');
    });

    await userEvent.keyboard(nextKey);
    await waitFor(() => {
      expect(screen.getByText('Status').closest('a')).toHaveClass('bp5-active');
    });

    await userEvent.keyboard(prevKey);
    await waitFor(() => {
      expect(screen.getByText('Type').closest('a')).toHaveClass('bp5-active');
    });

    await userEvent.keyboard(nextKey);
    await waitFor(() => {
      expect(screen.getByText('Status').closest('a')).toHaveClass('bp5-active');
    });

    await userEvent.keyboard(nextKey);
    expect(input).toHaveFocus();

    await userEvent.keyboard(nextKey);
    await waitFor(() => {
      expect(screen.getByText('Type').closest('a')).toHaveClass('bp5-active');
    });

    await userEvent.keyboard(nextKey);
    await waitFor(() => {
      expect(screen.getByText('Status').closest('a')).toHaveClass('bp5-active');
    });

    await userEvent.keyboard(enterKey);

    await waitFor(() => {
      expect(input).toHaveFocus();
    });

    await userEvent.keyboard(nextKey);
    await userEvent.keyboard(nextKey);

    expect(screen.getByText('Inactive').closest('a')).toHaveClass('bp5-active');
    await userEvent.keyboard(enterKey);

    await waitFor(() => {
      expect(mockFilters[1]!.onSelect).toHaveBeenCalled();
    });
  };

  // eslint-disable-next-line jest/expect-expect
  test('keyboard navigation and selection with arrow keys', async () => {
    await testKeyboardNavigation('{ArrowDown}', '{ArrowUp}', '{Enter}');
  });

  // eslint-disable-next-line jest/expect-expect
  test('keyboard navigation and selection with Tab and Shift+Tab keys', async () => {
    await testKeyboardNavigation('{Tab}', '{Shift}{Tab}', ' ');
  });

  test('escape key behavior', async () => {
    render(<FilterDropdownButton filters={mockFilters} />);

    await userEvent.click(screen.getByRole('button'));
    expect(screen.getByRole('menu')).toBeVisible();

    const input = screen.getByLabelText('Search filters');
    expect(input).toHaveFocus();

    expect(screen.queryByText('Type 1')).toBeNull();

    await userEvent.keyboard('{ArrowDown}');

    await userEvent.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByText('Type 1')).toBeVisible();
    });

    await userEvent.keyboard('{Escape}');

    expect(screen.queryByText('Type 1')).toBeNull();

    await userEvent.keyboard('{Escape}');
    await waitFor(() => {
      expect(screen.queryByRole('menu')).not.toBeInTheDocument();
    });
  });
});
