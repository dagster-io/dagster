import React, {HTMLProps} from 'react';
import {Link, LinkProps} from 'react-router-dom';
import styled from 'styled-components/macro';

import {ColorsWIP} from './Colors';
import {IconWrapper} from './Icon';
import {FontFamily} from './styles';

interface TabsProps {
  children: Array<React.ReactElement<TabProps>>;
  selectedTabId?: string;
  onChange?: (selectedTabId: string) => void;
  size?: 'small' | 'large';
}

export const Tabs = styled(({selectedTabId, children, onChange, size = 'large', ...rest}) => {
  if (!(children instanceof Array) || children.some((c) => c.type !== Tab)) {
    throw new Error('Tabs must render Tab instances');
  }

  return (
    <div {...rest} role="tablist">
      {React.Children.map(children, (child) =>
        React.cloneElement(child, {
          selected: child.props.selected || child.props.id === selectedTabId,
          $size: size,
          ...(onChange
            ? {
                onClick: () => onChange(child.props.id),
              }
            : {}),
        }),
      )}
    </div>
  );
})<TabsProps>`
  display: flex;
  gap: 16px;
  font-size: ${({size}) => (size === 'small' ? '12px' : '14px')};
  line-height: ${({size}) => (size === 'small' ? '16px' : '20px')};
  font-weight: 600;
`;

interface TabProps {
  id: string;
  title: React.ReactNode;
  disabled?: boolean;
  selected?: boolean;
  count?: number | 'indeterminate';
  icon?: React.ReactNode;
  $size?: 'small' | 'large';

  // options for tab interaction if you opt not to use <Tabs onChange={}>
  to?: LinkProps<unknown>['to'];
  onClick?: (e: React.MouseEvent) => void;
}

export const Tab = styled(({id, title, count, icon, selected, disabled, to, onClick, ...rest}) => {
  const containerProps: Omit<HTMLProps<unknown>, 'ref'> = {
    role: 'tab',
    tabIndex: disabled ? -1 : 0,
    'aria-disabled': disabled,
    'aria-expanded': selected,
    'aria-selected': selected,
    onKeyDown: (e: React.KeyboardEvent) =>
      [' ', 'Return', 'Enter'].includes(e.key) &&
      e.currentTarget instanceof HTMLElement &&
      e.currentTarget.click(),
    onClick: (e: React.MouseEvent<any>) => {
      if (disabled) {
        e.preventDefault();
      } else if (onClick) {
        e.preventDefault();
        onClick?.(e);
      }
    },
    ...rest,
  };

  const content = (
    <>
      {title}
      {icon}
      {count !== undefined ? <Count>{count === 'indeterminate' ? '–' : count}</Count> : null}
    </>
  );

  return to ? (
    <Link {...containerProps} to={to}>
      {content}
    </Link>
  ) : (
    <button {...containerProps} type="button">
      {content}
    </button>
  );
})<TabProps>`
  background: none;
  border: none;
  font-size: 14px;
  line-height: 20px;
  font-weight: 600;
  padding: ${({$size}) => ($size === 'small' ? '10px 0' : '16px 0')};
  box-shadow: ${({selected}) => (selected ? ColorsWIP.Blue500 : 'transparent')} 0 -2px 0 inset;
  display: flex;
  align-items: center;
  gap: 6px;

  &,
  & a {
    cursor: default;
    user-select: none;
    color: ${({selected, disabled}) =>
      selected ? ColorsWIP.Blue500 : disabled ? ColorsWIP.Gray300 : ColorsWIP.Gray700};
  }

  & ${IconWrapper} {
    color: ${({selected, disabled}) =>
      selected ? ColorsWIP.Blue500 : disabled ? ColorsWIP.Gray300 : ''};
  }

  /* Focus outline only when using keyboard, not when focusing via mouse. */
  &:focus {
    outline: none !important;
    box-shadow: ${({selected, disabled}) =>
        selected ? ColorsWIP.Blue500 : disabled ? 'transparent' : ColorsWIP.Blue200}
      0 -2px 0 inset;
  }

  &:hover {
    &,
    a {
      text-decoration: none;
      color: ${({selected, disabled}) =>
        selected ? ColorsWIP.Blue700 : disabled ? ColorsWIP.Gray300 : ColorsWIP.Blue700};
    }
    ${IconWrapper} {
      color: ${({selected, disabled}) =>
        selected ? ColorsWIP.Blue700 : disabled ? ColorsWIP.Gray300 : ''};
    }
  }
`;

const Count = styled.div`
  display: inline;
  font-family: ${FontFamily.monospace};
  font-size: 14px;
  font-weight: 500;
  letter-spacing: -0.02%;
  padding: 0 4px;
  color: ${ColorsWIP.Gray900};
  background: ${ColorsWIP.Gray100};
`;
