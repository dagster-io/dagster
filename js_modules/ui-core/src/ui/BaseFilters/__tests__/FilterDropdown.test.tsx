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
  it('displays filter categories initially', () => {
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

  it('searches and displays matching filters', async () => {
    render(
      <FilterDropdown
        filters={mockFilters}
        setIsOpen={jest.fn()}
        setPortaledElements={jest.fn()}
      />,
    );
    const searchInput = screen.getByPlaceholderText('Search filters...');
    await userEvent.type(searchInput, 'type');
    expect(await screen.findByText('Type 1')).toBeInTheDocument();
    expect(await screen.findByText('Type 2')).toBeInTheDocument();
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    await waitFor(() => expect(mockFilters[0]!.getResults).toHaveBeenCalledWith('type'));
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    await waitFor(() => expect(mockFilters[1]!.getResults).toHaveBeenCalledWith('type'));
  });

  it('displays no results when no filters match', async () => {
    render(
      <FilterDropdown
        filters={mockFilters}
        setIsOpen={jest.fn()}
        setPortaledElements={jest.fn()}
      />,
    );
    const searchInput = screen.getByPlaceholderText('Search filters...');
    await userEvent.type(searchInput, 'nonexistent');
    expect(await screen.findByText('No results')).toBeInTheDocument();
  });
});

describe('FilterDropdownButton', () => {
  it('opens and closes the dropdown on click', async () => {
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

  it('closes the dropdown when clicking outside', async () => {
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
    const user = userEvent.setup();
    render(<FilterDropdownButton filters={mockFilters} />);

    await user.click(screen.getByRole('button'));
    expect(screen.getByRole('menu')).toBeInTheDocument();

    const input = screen.getByLabelText('Search filters');
    expect(input).toHaveFocus();

    await user.keyboard(nextKey);
    await waitFor(() => {
      expect(screen.getByRole('menuitem', {name: /type/i}).getAttribute('data-active')).toBe(
        'true',
      );
    });

    await user.keyboard(nextKey);
    await waitFor(() => {
      expect(screen.getByRole('menuitem', {name: /status/i}).getAttribute('data-active')).toBe(
        'true',
      );
    });

    await user.keyboard(prevKey);
    await waitFor(() => {
      expect(screen.getByRole('menuitem', {name: /type/i}).getAttribute('data-active')).toBe(
        'true',
      );
    });

    await user.keyboard(nextKey);
    await waitFor(() => {
      expect(screen.getByRole('menuitem', {name: /status/i}).getAttribute('data-active')).toBe(
        'true',
      );
    });

    await user.keyboard(nextKey);
    expect(input).toHaveFocus();

    await user.keyboard(nextKey);
    await waitFor(() => {
      expect(screen.getByRole('menuitem', {name: /type/i}).getAttribute('data-active')).toBe(
        'true',
      );
    });

    await user.keyboard(nextKey);
    await waitFor(() => {
      expect(screen.getByRole('menuitem', {name: /status/i}).getAttribute('data-active')).toBe(
        'true',
      );
    });

    await user.keyboard(enterKey);

    await waitFor(() => {
      expect(input).toHaveFocus();
    });

    await user.keyboard(nextKey);
    await user.keyboard(nextKey);

    expect(screen.getByRole('menuitem', {name: /inactive/i}).getAttribute('data-active')).toBe(
      'true',
    );
    await user.keyboard(enterKey);

    await waitFor(() => {
      expect(mockFilters[1]?.onSelect).toHaveBeenCalled();
    });
  };

  // eslint-disable-next-line jest/expect-expect
  it('keyboard navigation and selection with arrow keys', async () => {
    await testKeyboardNavigation('{ArrowDown}', '{ArrowUp}', '{Enter}');
  });

  // eslint-disable-next-line jest/expect-expect
  it('keyboard navigation and selection with Tab and Shift+Tab keys', async () => {
    await testKeyboardNavigation('{Tab}', '{Shift}{Tab}', ' ');
  });

  it('escape key behavior', async () => {
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
