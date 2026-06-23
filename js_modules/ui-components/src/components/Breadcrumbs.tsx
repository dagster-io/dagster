import clsx from 'clsx';
import React, {ReactNode, useLayoutEffect, useRef, useState} from 'react';

import {HoverButton} from './HoverButton';
import {Icon} from './Icon';
import {Menu, MenuItem} from './Menu';
import {Popover} from './Popover';
import styles from './css/Breadcrumbs.module.css';

export interface BreadcrumbProps {
  text: string | ReactNode;
  href?: string;
  onClick?: () => void;
}

interface BreadcrumbsProps {
  items: BreadcrumbProps[];
  breadcrumbRenderer?: (props: BreadcrumbProps) => ReactNode;
  currentBreadcrumbRenderer?: (props: BreadcrumbProps) => ReactNode;
  overflowRenderer?: (props: BreadcrumbProps) => ReactNode;
  className?: string;
}

const OVERFLOW_ITEM_WIDTH = 40;

const Separator = () => <Icon name="chevron_right" className={styles.separator} />;

const defaultRenderer = ({text, href, onClick}: BreadcrumbProps) => {
  if (href) {
    return (
      <a className={styles.breadcrumb} href={href} onClick={onClick}>
        {text}
      </a>
    );
  }
  if (onClick) {
    return (
      <button type="button" className={styles.breadcrumbButton} onClick={onClick}>
        {text}
      </button>
    );
  }
  return <span className={styles.breadcrumb}>{text}</span>;
};

export const Breadcrumbs = ({
  items,
  breadcrumbRenderer = defaultRenderer,
  currentBreadcrumbRenderer,
  overflowRenderer,
  className,
}: BreadcrumbsProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const [collapseCount, setCollapseCount] = useState(0);
  const itemsLengthRef = useRef(items.length);
  const widthRef = useRef(0);
  const stableRef = useRef(false);

  // Reset collapse count when items change length.
  if (items.length !== itemsLengthRef.current) {
    itemsLengthRef.current = items.length;
    stableRef.current = false;
    setCollapseCount(0);
  }

  // Watch the outer container for width changes. The container has
  // overflow:hidden and is constrained by the parent layout. The inner
  // <ul> uses width:max-content so it always reflects its true content
  // width regardless of the container — this lets us reliably compare
  // content width vs available width.
  useLayoutEffect(() => {
    const container = containerRef.current;
    if (!container) {
      return;
    }

    const observer = new ResizeObserver(() => {
      const w = container.clientWidth;
      if (w !== widthRef.current) {
        widthRef.current = w;
        stableRef.current = false;
        setCollapseCount(0);
      }
    });

    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  // Single-pass measurement: when all items are rendered (collapseCount=0),
  // compare the <ul>'s natural width (max-content) against the container's
  // constrained width. If overflowing, measure each <li> and calculate how
  // many to collapse in one shot.
  useLayoutEffect(() => {
    if (stableRef.current) {
      return;
    }
    const container = containerRef.current;
    const list = listRef.current;
    if (!container || !list || items.length <= 2) {
      stableRef.current = true;
      return;
    }
    if (collapseCount !== 0) {
      return;
    }

    const availableWidth = container.clientWidth;
    const contentWidth = list.getBoundingClientRect().width;

    if (contentWidth <= availableWidth) {
      stableRef.current = true;
      return;
    }

    // Measure each item's rendered width.
    const children = Array.from(list.children) as HTMLElement[];
    const widths = children.map((child) => child.getBoundingClientRect().width);

    // Budget: available width minus first item, minus overflow button estimate.
    const firstWidth = widths[0] ?? 0;
    const budget = availableWidth - firstWidth - OVERFLOW_ITEM_WIDTH;

    // Greedily add trailing items (from the end) until budget is exhausted.
    let used = 0;
    let keepFromEnd = 0;
    for (let i = widths.length - 1; i >= 1; i--) {
      const w = widths[i] ?? 0;
      if (used + w <= budget) {
        used += w;
        keepFromEnd++;
      } else {
        break;
      }
    }

    keepFromEnd = Math.max(keepFromEnd, 1);
    setCollapseCount(Math.max(0, items.length - 1 - keepFromEnd));
    stableRef.current = true;
  }, [items.length, collapseCount]);

  const lastIndex = items.length - 1;
  const renderItem = (item: BreadcrumbProps, index: number) => {
    if (index === lastIndex && currentBreadcrumbRenderer) {
      return currentBreadcrumbRenderer(item);
    }
    return breadcrumbRenderer(item);
  };

  const firstItem = items[0];
  if (!firstItem) {
    return null;
  }

  if (collapseCount === 0 || items.length <= 2) {
    return (
      <div ref={containerRef} className={clsx(styles.breadcrumbsContainer, className)}>
        <ul ref={listRef} className={styles.breadcrumbs}>
          {items.map((item, i) => (
            <li key={i} className={styles.breadcrumbItem}>
              {i > 0 ? <Separator /> : null}
              {renderItem(item, i)}
            </li>
          ))}
        </ul>
      </div>
    );
  }

  const collapsedItems = items.slice(1, 1 + collapseCount);
  const visibleTail = items.slice(1 + collapseCount);

  return (
    <div ref={containerRef} className={clsx(styles.breadcrumbsContainer, className)}>
      <ul ref={listRef} className={styles.breadcrumbs}>
        <li className={styles.breadcrumbItem}>{renderItem(firstItem, 0)}</li>
        <li className={styles.breadcrumbItem}>
          <Separator />
          <Popover
            placement="bottom-start"
            content={
              <Menu>
                {collapsedItems.map((item, i) =>
                  overflowRenderer ? (
                    <React.Fragment key={i}>{overflowRenderer(item)}</React.Fragment>
                  ) : (
                    <MenuItem key={i} text={item.text} onClick={item.onClick} />
                  ),
                )}
              </Menu>
            }
          >
            <HoverButton>
              <Icon name="more_horiz" />
            </HoverButton>
          </Popover>
        </li>
        {visibleTail.map((item, i) => {
          const originalIndex = 1 + collapseCount + i;
          return (
            <li key={originalIndex} className={styles.breadcrumbItem}>
              <Separator />
              {renderItem(item, originalIndex)}
            </li>
          );
        })}
      </ul>
    </div>
  );
};
