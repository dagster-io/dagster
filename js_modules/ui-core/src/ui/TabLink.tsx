import {TabStyleProps, getTabA11yProps, getTabContent, tabStyles} from '@dagster-io/ui-components';
import clsx from 'clsx';
import * as React from 'react';
import {Link, LinkProps} from 'react-router-dom';

interface TabLinkProps extends TabStyleProps, Omit<LinkProps, 'title'> {
  title?: React.ReactNode;
}

export const TabLink = React.forwardRef<HTMLAnchorElement, TabLinkProps>(
  ({disabled, selected, size, count, icon, title, className, to, ...rest}, ref) => {
    const containerProps = getTabA11yProps({selected, disabled});
    const content = getTabContent({disabled, selected, size, count, icon, title});
    const titleText = typeof title === 'string' ? title : undefined;

    return (
      <Link
        ref={ref}
        to={disabled ? '#' : to}
        title={titleText}
        className={clsx(
          tabStyles.tab,
          selected && tabStyles.selected,
          disabled && tabStyles.disabled,
          size === 'small' && tabStyles.small,
          className,
        )}
        {...containerProps}
        {...rest}
      >
        {content}
      </Link>
    );
  },
);
