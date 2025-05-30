import {CSSProperties, ChangeEvent, HTMLProps, ReactNode, forwardRef} from 'react';

import {Checkbox} from './Checkbox';
import styles from './css/ListItem.module.css';
import {directionalSpacingToValues} from './directionalSpacingToValues';
import {DirectionalSpacing} from './types';

interface Props {
  index: number;
  checked?: boolean;
  onToggle?: (checked: boolean) => void;
  href: string;
  renderLink: (props: HTMLProps<HTMLAnchorElement>) => ReactNode;
  padding?: DirectionalSpacing;
  left: ReactNode;
  right: ReactNode;
}

const defaultRenderLink = ({href, ...props}: HTMLProps<HTMLAnchorElement>): ReactNode => (
  <a href={href} {...props} />
);

const DEFAULT_PADDING: DirectionalSpacing = {
  vertical: 12,
  horizontal: 24,
};

export const ListItem = forwardRef<HTMLDivElement, Props>((props, ref) => {
  const {
    index,
    checked = false,
    padding = DEFAULT_PADDING,
    onToggle,
    href,
    renderLink,
    left,
    right,
  } = props;

  const link = renderLink ?? defaultRenderLink;
  const {top, right: rightPadding, bottom, left: leftPadding} = directionalSpacingToValues(padding);

  return (
    <div
      className={styles.listItem}
      style={
        {
          '--spacing-top': `${top}px`,
          '--spacing-bottom': `${bottom}px`,
          '--spacing-left': `${leftPadding}px`,
        } as CSSProperties
      }
      data-index={index}
      ref={ref}
    >
      {onToggle ? (
        <div className={styles.checkboxContainer}>
          <Checkbox
            format="check"
            checked={checked}
            size="small"
            onChange={(e: ChangeEvent<HTMLInputElement>) => onToggle(e.target.checked)}
          />
        </div>
      ) : null}
      {link({
        href,
        className: styles.listItemAnchor,
        children: left,
      })}
      <div
        style={{'--spacing-right': `${rightPadding}px`} as CSSProperties}
        className={styles.right}
      >
        {right}
      </div>
    </div>
  );
});
