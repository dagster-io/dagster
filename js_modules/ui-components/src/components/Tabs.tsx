import clsx from 'clsx';
import * as React from 'react';

import styles from './css/Tabs.module.css';

export {default as tabStyles} from './css/Tabs.module.css';

export interface TabStyleProps {
  disabled?: boolean;
  selected?: boolean;
  count?: number | 'indeterminate' | null;
  icon?: React.ReactNode;
  title?: React.ReactNode;
  size?: 'small' | 'large';
}

export const getTabA11yProps = (props: {selected?: boolean; disabled?: boolean}) => {
  const {selected, disabled} = props;
  return {
    role: 'tab' as const,
    tabIndex: disabled ? -1 : 0,
    'aria-disabled': disabled,
    'aria-expanded': selected,
    'aria-selected': selected,
  };
};

export const getTabContent = (props: TabStyleProps & {title?: React.ReactNode}) => {
  const {title, count, icon} = props;
  return (
    <>
      {title}
      {icon}
      {count !== undefined ? (
        <div className={clsx(styles.count, props.disabled && styles.disabled)}>
          {count === 'indeterminate' ? '\u2013' : count}
        </div>
      ) : null}
    </>
  );
};

interface TabProps extends TabStyleProps, Omit<React.ComponentPropsWithoutRef<'button'>, 'title'> {}

export const Tab = ({
  selected,
  disabled,
  size,
  count,
  icon,
  title,
  className,
  ...rest
}: TabProps) => {
  const containerProps = getTabA11yProps({selected, disabled});
  const content = getTabContent({selected, disabled, size, count, icon, title});
  const titleText = typeof title === 'string' ? title : undefined;

  return (
    <button
      className={clsx(
        styles.tab,
        selected && styles.selected,
        disabled && styles.disabled,
        size === 'small' && styles.small,
        className,
      )}
      {...containerProps}
      disabled={disabled}
      {...rest}
      title={titleText}
      type="button"
    >
      {content}
    </button>
  );
};

interface TabsProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'onChange'> {
  children: React.ReactNode;
  selectedTabId?: string;
  onChange?: (selectedTabId: any) => void;
  size?: 'small' | 'large';
}

export const Tabs = ({
  selectedTabId,
  children,
  onChange,
  size = 'large',
  className,
  ...rest
}: TabsProps) => {
  return (
    <div
      className={clsx(styles.tabs, size === 'small' && styles.small, className)}
      role="tablist"
      {...rest}
    >
      {React.Children.map(children, (child) =>
        React.isValidElement<TabProps>(child)
          ? React.cloneElement(child, {
              selected: child.props.selected || child.props.id === selectedTabId,
              size,
              ...(onChange
                ? {
                    onClick: () => onChange(child.props.id ?? ''),
                  }
                : {}),
            })
          : null,
      )}
    </div>
  );
};
