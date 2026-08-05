import {Icon} from '@dagster-io/ui-components';
import * as Collapsible from '@radix-ui/react-collapsible';
import clsx from 'clsx';
import * as React from 'react';

import styles from './css/SidebarComponents.module.css';
import {useStateWithStorage} from '../hooks/useStateWithStorage';

interface ISidebarSectionProps {
  children: React.ReactNode;
  title: string;
  collapsedByDefault?: boolean;
}

export const SidebarSection = (props: ISidebarSectionProps) => {
  const {title, collapsedByDefault, children} = props;
  const [open, setOpen] = useStateWithStorage<boolean>(`sidebar-${title}`, (storedValue) =>
    storedValue === true || storedValue === false ? storedValue : !collapsedByDefault,
  );

  return (
    <Collapsible.Root open={open} onOpenChange={setOpen}>
      <Collapsible.Trigger asChild>
        <div className={styles.collapsingHeaderBar}>
          <div className={styles.sidebarTitleTextWrap}>{title}</div>
          <Icon
            size={24}
            name="arrow_drop_down"
            style={{transform: open ? 'rotate(0)' : 'rotate(-90deg)'}}
          />
        </div>
      </Collapsible.Trigger>
      <Collapsible.Content style={{overflowX: 'auto'}}>
        <div>{children}</div>
      </Collapsible.Content>
    </Collapsible.Root>
  );
};

export const SidebarTitle = ({
  children,
  className,
  ...rest
}: React.HTMLAttributes<HTMLHeadingElement>) => (
  <h3 className={clsx(styles.sidebarTitle, className)} {...rest}>
    {children}
  </h3>
);

export const SectionHeader = ({
  children,
  className,
  ...rest
}: React.HTMLAttributes<HTMLHeadingElement>) => (
  <h4 className={clsx(styles.sectionHeader, className)} {...rest}>
    {children}
  </h4>
);

export const SectionSmallHeader = ({
  children,
  className,
  ...rest
}: React.HTMLAttributes<HTMLHeadingElement>) => (
  <h4 className={clsx(styles.sectionSmallHeader, className)} {...rest}>
    {children}
  </h4>
);

export const SidebarSubhead = ({children}: {children?: React.ReactNode}) => (
  <div className={styles.sidebarSubhead}>{children}</div>
);

export const SectionItemContainer = ({children}: {children?: React.ReactNode}) => (
  <div className={styles.sectionItemContainer}>{children}</div>
);
