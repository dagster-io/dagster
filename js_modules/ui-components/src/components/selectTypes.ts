/**
 * Type definitions for Select and Suggest components.
 * These replace the types previously imported from @blueprintjs/select.
 */

export interface ItemModifiers {
  active: boolean;
  disabled: boolean;
  matchesPredicate: boolean;
}

export interface ItemRendererProps {
  handleClick: React.MouseEventHandler<HTMLElement>;
  handleFocus: () => void;
  index: number;
  modifiers: ItemModifiers;
  query: string;
}

export type ItemRenderer<T> = (item: T, props: ItemRendererProps) => React.JSX.Element | null;

export interface ItemListRendererProps<T> {
  activeItem: T | null;
  filteredItems: T[];
  items: T[];
  query: string;
  renderItem: (item: T, index: number) => React.JSX.Element | null;
  itemsParentRef: React.Ref<any>;
  menuProps: React.HTMLAttributes<HTMLElement>;
}

export type ItemListRenderer<T> = (props: ItemListRendererProps<T>) => React.JSX.Element | null;

export type ItemPredicate<T> = (query: string, item: T, index?: number) => boolean;

export type ItemListPredicate<T> = (query: string, items: T[]) => T[];

/** Popper.js placement values accepted by Blueprint Popover. */
type Placement =
  | 'auto'
  | 'auto-start'
  | 'auto-end'
  | 'top'
  | 'top-start'
  | 'top-end'
  | 'bottom'
  | 'bottom-start'
  | 'bottom-end'
  | 'right'
  | 'right-start'
  | 'right-end'
  | 'left'
  | 'left-start'
  | 'left-end';

/** Blueprint PopoverPosition values (uses left/right instead of start/end). */
type PopoverPosition =
  | 'auto'
  | 'auto-start'
  | 'auto-end'
  | 'top'
  | 'top-left'
  | 'top-right'
  | 'bottom'
  | 'bottom-left'
  | 'bottom-right'
  | 'left'
  | 'left-top'
  | 'left-bottom'
  | 'right'
  | 'right-top'
  | 'right-bottom';

/** Popover configuration accepted by Select and Suggest. */
export interface SelectPopoverProps {
  position?: PopoverPosition;
  placement?: Placement;
  matchTargetWidth?: boolean;
  targetTagName?: keyof React.JSX.IntrinsicElements;
  targetProps?: React.HTMLAttributes<HTMLElement>;
  usePortal?: boolean;
  onOpened?: (node: HTMLElement) => void;
  onClosed?: (node: HTMLElement) => void;
  onInteraction?: (nextOpen: boolean, e?: React.SyntheticEvent<HTMLElement>) => void;
  modifiers?: Record<string, unknown>;
  popoverClassName?: string;
  className?: string;
  minimal?: boolean;
}

/** Shared props between Select and Suggest. */
export interface BaseListProps<T> {
  items: T[];
  itemRenderer: ItemRenderer<T>;
  onItemSelect: (item: T, event?: React.MouseEvent<HTMLElement>) => void;
  itemPredicate?: ItemPredicate<T>;
  itemListPredicate?: ItemListPredicate<T>;
  activeItem?: T | null;
  noResults?: React.ReactNode;
  disabled?: boolean;
  query?: string;
  onQueryChange?: (query: string) => void;
  resetOnQuery?: boolean;
  resetOnSelect?: boolean;
  resetOnClose?: boolean;
  popoverProps?: SelectPopoverProps;
}
