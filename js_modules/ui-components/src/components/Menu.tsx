import clsx from 'clsx';
import {
  CSSProperties,
  FocusEventHandler,
  HTMLProps,
  KeyboardEvent,
  MouseEvent,
  ReactNode,
  forwardRef,
} from 'react';

import {Icon, IconName} from './Icon';
import {Intent} from './Intent';
import styles from './css/Menu.module.css';

const intentToClassName = (intent: Intent) => {
  return clsx(
    intent === 'primary' && styles.primary,
    intent === 'danger' && styles.danger,
    intent === 'success' && styles.success,
    intent === 'warning' && styles.warning,
    intent === 'none' && styles.none,
  );
};

// ===== MENU =====

export const Menu = forwardRef<HTMLUListElement, HTMLProps<HTMLUListElement>>((props, ref) => {
  const {className, children, ...rest} = props;
  return (
    <ul {...rest} role="menu" ref={ref} className={clsx(styles.menu, className)}>
      {children}
    </ul>
  );
});

Menu.displayName = 'Menu';

export interface MenuItemContentsProps {
  icon?: IconName | ReactNode;
  intent?: Intent;
  text?: ReactNode;
  right?: string | ReactNode;
  className?: string;
  active?: boolean;
  disabled?: boolean;
  style?: CSSProperties;
}

export const MenuItemContents = (props: MenuItemContentsProps) => {
  const {
    icon,
    intent = 'none',
    text,
    right,
    className,
    active = false,
    disabled = false,
    style,
  } = props;

  const iconElement = () => {
    if (typeof icon === 'string') {
      return <Icon name={icon as IconName} className={styles.menuItemIcon} />;
    }
    return icon;
  };

  return (
    <div
      className={clsx(
        styles.menuItem,
        active && styles.menuItemActive,
        disabled && styles.menuItemDisabled,
        intentToClassName(intent),
        className,
      )}
      style={style}
    >
      {icon ? iconElement() : null}
      <span className={styles.menuItemText}>{text}</span>
      {right ? <span className={styles.menuItemRight}>{right}</span> : null}
    </div>
  );
};

// ===== MENUITEM =====

export interface CommonMenuItemProps {
  icon?: IconName | ReactNode;
  intent?: Intent;
  style?: CSSProperties;
  className?: string;
}

interface MenuItemProps extends CommonMenuItemProps {
  text: ReactNode;
  disabled?: boolean;
  active?: boolean;
  onClick?: (e: MouseEvent<HTMLButtonElement>) => void;
  onMouseDown?: (e: MouseEvent<HTMLButtonElement>) => void;
  onFocus?: FocusEventHandler<HTMLButtonElement>;
  right?: string | ReactNode;
  shouldDismissPopover?: boolean;
  tabIndex?: number;
}

export const MenuItem = forwardRef<HTMLLIElement, MenuItemProps>((props, ref) => {
  const {
    text,
    icon,
    intent = 'none',
    disabled = false,
    active = false,
    onClick,
    onMouseDown,
    onFocus,
    right,
    shouldDismissPopover = true,
    style,
    tabIndex = 0,
    className,
    ...rest
  } = props;

  const handleClick = (e: MouseEvent<HTMLButtonElement>) => {
    if (disabled) {
      e.preventDefault();
      e.stopPropagation();
      return;
    }
    onClick?.(e);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLButtonElement>) => {
    if (!disabled && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault();
      e.currentTarget.click();
    }
  };

  return (
    <li {...rest} role="none" ref={ref} className={styles.menuItemWrapper}>
      <button
        type="button"
        role="menuitem"
        aria-disabled={disabled}
        tabIndex={disabled ? -1 : tabIndex}
        data-active={active}
        disabled={disabled}
        className={clsx(
          styles.menuItemButton,
          // Below is a Blueprint hack to close `Popover` on click, until we've refactored
          // away from using Blueprint `Popover`.
          shouldDismissPopover ? 'bp5-popover-dismiss' : null,
        )}
        onClick={handleClick}
        onMouseDown={onMouseDown}
        onKeyDown={handleKeyDown}
        onFocus={onFocus}
      >
        <MenuItemContents
          icon={icon}
          intent={intent}
          text={text}
          right={right}
          className={className}
          active={active}
          disabled={disabled}
          style={style}
        />
      </button>
    </li>
  );
});

MenuItem.displayName = 'MenuItem';

// ===== MENUITEMFORINTERACTIVECONTENT =====

interface MenuItemForInteractiveContentProps extends CommonMenuItemProps {
  children: ReactNode;
}

/**
 * Use MenuItemForInteractiveContent when you need to include interactive elements
 * (like checkboxes, radio buttons, or other inputs) within a menu item.
 * This component renders as a div instead of a button to support nested interactive content.
 *
 * For standard menu actions, use MenuItem instead.
 *
 * Example:
 * <MenuItemForInteractiveContent>
 *   <Checkbox label="Show completed" />
 * </MenuItemForInteractiveContent>
 */
export const MenuItemForInteractiveContent = forwardRef<
  HTMLLIElement,
  MenuItemForInteractiveContentProps
>((props, ref) => {
  const {children, intent = 'none', style, className, ...rest} = props;
  return (
    <li {...rest} role="none" ref={ref} className={styles.menuItemWrapper}>
      <div
        role="menuitem"
        className={clsx(styles.menuItem, intentToClassName(intent), className)}
        style={style}
      >
        {children}
      </div>
    </li>
  );
});

MenuItemForInteractiveContent.displayName = 'MenuItemForInteractiveContent';

// ===== MENUEXTERNALLINK =====

interface MenuExternalLinkProps extends CommonMenuItemProps {
  href: string;
  text: ReactNode;
  right?: string | ReactNode;
  tabIndex?: number;
  download?: boolean | string;
  onClick?: (e: MouseEvent<HTMLAnchorElement>) => void;
}

/**
 * If you want to use a menu item as an external link, use `MenuExternalLink` and provide an `href` prop.
 * For internal links with react-router, use `MenuLink` from ui-core.
 */
export const MenuExternalLink = forwardRef<HTMLLIElement, MenuExternalLinkProps>((props, ref) => {
  const {
    href,
    text,
    icon,
    intent = 'none',
    right = '',
    style,
    tabIndex = 0,
    className,
    download,
    onClick,
    ...rest
  } = props;

  return (
    <li {...rest} role="none" ref={ref} className={styles.menuItemWrapper}>
      <a
        href={href}
        role="menuitem"
        tabIndex={tabIndex}
        className={styles.menuItemAnchor}
        onClick={onClick}
        download={download}
        target="_blank"
        rel="noreferrer nofollow"
      >
        <MenuItemContents
          icon={icon}
          intent={intent}
          text={text}
          right={right}
          className={className}
          style={style}
        />
      </a>
    </li>
  );
});

MenuExternalLink.displayName = 'MenuExternalLink';

// ===== MENUDIVIDER =====

interface MenuDividerProps {
  title?: ReactNode;
  className?: string;
}

export const MenuDivider = (props: MenuDividerProps) => {
  const {title, className} = props;
  const allClassNames = clsx(title ? styles.menuHeader : styles.menuDivider, className);
  return (
    <li role="separator" className={allClassNames}>
      {title ? <h6 className={styles.menuHeaderTitle}>{title}</h6> : null}
    </li>
  );
};
