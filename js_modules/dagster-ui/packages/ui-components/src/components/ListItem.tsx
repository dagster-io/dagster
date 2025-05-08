import {ChangeEvent, HTMLProps, ReactNode, forwardRef} from 'react';

import {Checkbox} from './Checkbox';
import styles from './css/ListItem.module.css';

interface Props {
  index: number;
  checked?: boolean;
  onToggle?: (checked: boolean) => void;
  href: string;
  renderLink: (props: HTMLProps<HTMLAnchorElement>) => ReactNode;
  left: ReactNode;
  right: ReactNode;
}

const defaultRenderLink = ({href, ...props}: HTMLProps<HTMLAnchorElement>): ReactNode => (
  <a href={href} {...props} />
);

export const ListItem = forwardRef<HTMLDivElement, Props>(
  ({index, checked = false, onToggle, href, renderLink, left, right}, ref) => {
    const link = renderLink ?? defaultRenderLink;
    return (
      <div className={styles.listItem} data-index={index} ref={ref}>
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
        {link({href, className: styles.listItemAnchor, children: left})}
        <div className={styles.right}>{right}</div>
      </div>
    );
  },
);
