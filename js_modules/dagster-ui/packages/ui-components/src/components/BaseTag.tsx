import * as React from 'react';
import styled from 'styled-components';

import {Colors} from './Color';
import {IconWrapper} from './Icon';
import {SpinnerWrapper} from './Spinner';

interface Props {
  fillColor?: string;
  textColor?: string;
  icon?: React.ReactNode;
  interactive?: boolean;
  rightIcon?: React.ReactNode;
  label?: React.ReactNode;
  tooltipText?: string;
}

const BaseTagTooltipStyle: React.CSSProperties = {
  fontSize: 12,
  lineHeight: '16px',
  alignItems: 'center',
  padding: '4px 8px',
  userSelect: 'text',
  pointerEvents: 'none',
  borderRadius: 8,
  border: 'none',
  top: -9,
  left: -13,
};

export const BaseTag = (props: Props) => {
  const {
    fillColor = Colors.backgroundDefault(),
    textColor = Colors.textDefault(),
    icon,
    interactive = false,
    rightIcon,
    label,
    tooltipText,
  } = props;
  return (
    <StyledTag $fillColor={fillColor} $interactive={interactive} $textColor={textColor}>
      {icon || null}
      {label !== undefined && label !== null ? (
        <span
          data-tooltip={typeof label === 'string' ? label : tooltipText}
          data-tooltip-style={JSON.stringify({
            ...BaseTagTooltipStyle,
            backgroundColor: Colors.tooltipBackground(),
            color: Colors.tooltipText(),
          })}
        >
          {label}
        </span>
      ) : null}
      {rightIcon || null}
    </StyledTag>
  );
};

interface StyledTagProps {
  $fillColor: string;
  $interactive: boolean;
  $textColor: string;
}

export const StyledTag = styled.div<StyledTagProps>`
  background-color: ${({$fillColor}) => $fillColor};
  border-radius: 8px;
  color: ${({$textColor}) => $textColor};
  cursor: ${({$interactive}) => ($interactive ? 'pointer' : 'inherit')};
  display: inline-flex;
  flex-direction: row;
  font-size: 12px;
  line-height: 16px;
  align-items: center;
  padding: 4px 8px;
  user-select: none;
  transition: filter 100ms linear;
  max-width: 100%;

  & > span {
    max-width: 400px;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }

  > ${IconWrapper}:first-child, > ${SpinnerWrapper}:first-child {
    margin-right: 4px;
    margin-left: -4px;
  }

  > ${IconWrapper}:last-child, > ${SpinnerWrapper}:last-child {
    margin-left: 4px;
    margin-right: -4px;
  }

  > ${IconWrapper}:first-child:last-child, > ${SpinnerWrapper}:first-child:last-child {
    margin: 0 -4px;
  }
`;
