import * as React from 'react';
import styled, {css} from 'styled-components';

import {
  colorAccentBlue,
  colorAccentGray,
  colorBackgroundGray,
  colorTextDefault,
  colorTextDisabled,
  colorTextLight,
} from '../theme/color';

import {IconWrapper} from './Icon';
import {FontFamily} from './styles';

export interface TabStyleProps {
  disabled?: boolean;
  selected?: boolean;
  count?: number | 'indeterminate' | null;
  icon?: React.ReactNode;
  title?: React.ReactNode;
  $size?: 'small' | 'large';
}

export const getTabA11yProps = (props: {selected?: boolean; disabled?: boolean}) => {
  const {selected, disabled} = props;
  return {
    role: 'tab',
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
        <Count $disabled={!!props.disabled}>{count === 'indeterminate' ? '\u2013' : count}</Count>
      ) : null}
    </>
  );
};

const Count = styled.div<{$disabled: boolean}>`
  display: inline;
  font-family: ${FontFamily.monospace};
  font-size: 14px;
  font-weight: 500;
  letter-spacing: -0.02%;
  padding: 0 6px;
  color: ${({$disabled}) => ($disabled ? colorTextDisabled() : colorTextDefault())};
  background: ${colorBackgroundGray()};
  border-radius: 4px;
`;

export const tabCSS = css<TabStyleProps>`
  background: none;
  border: none;
  font-size: 14px;
  line-height: 20px;
  font-weight: 600;
  padding: ${({$size}) => ($size === 'small' ? '10px 0' : '16px 0')};
  box-shadow: ${({selected}) => (selected ? colorAccentBlue() : 'transparent')} 0 -2px 0 inset;
  display: flex;
  align-items: center;
  cursor: pointer;
  gap: 6px;

  &,
  & a {
    cursor: pointer;
    user-select: none;
    color: ${({selected, disabled}) =>
      selected ? colorAccentBlue() : disabled ? colorTextDisabled() : colorTextLight()};
  }

  ${({disabled}) =>
    disabled
      ? css`
          & ${IconWrapper} {
            background-color: ${colorTextDisabled()};
          }
        `
      : null}

  /* Focus outline only when using keyboard, not when focusing via mouse. */
  &:focus {
    outline: none !important;
    box-shadow: ${({selected, disabled}) =>
        selected ? colorAccentBlue() : disabled ? 'transparent' : colorAccentGray()}
      0 -2px 0 inset;
  }

  &:hover {
    &,
    a {
      text-decoration: none;
      color: ${({selected, disabled}) =>
        selected ? colorAccentBlue() : disabled ? colorTextDisabled() : colorTextLight()};
    }

    ${({disabled}) => (disabled ? `color: ${colorTextDisabled()};` : null)}
  }
`;

interface TabProps extends TabStyleProps, Omit<React.ComponentPropsWithoutRef<'button'>, 'title'> {}

export const Tab = styled((props: TabProps) => {
  const containerProps = getTabA11yProps(props);
  const content = getTabContent(props);

  const titleText = typeof props.title === 'string' ? props.title : undefined;

  return (
    <button {...props} {...containerProps} title={titleText} type="button">
      {content}
    </button>
  );
})<TabStyleProps>`
  ${tabCSS}
`;

interface TabsProps {
  children: Array<React.ReactElement<TabProps>>;
  selectedTabId?: string;
  onChange?: (selectedTabId: string) => void;
  size?: 'small' | 'large';
}

export const Tabs = styled(({selectedTabId, children, onChange, size = 'large', ...rest}) => {
  return (
    <div {...rest} role="tablist">
      {React.Children.map(children, (child) =>
        child
          ? React.cloneElement(child, {
              selected: child.props.selected || child.props.id === selectedTabId,
              $size: size,
              ...(onChange
                ? {
                    onClick: () => onChange(child.props.id),
                  }
                : {}),
            })
          : null,
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
