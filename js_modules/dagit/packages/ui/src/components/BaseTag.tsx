import * as React from 'react';
import styled from 'styled-components/macro';

import {Colors} from './Colors';
import {IconWrapper} from './Icon';

interface Props {
  fillColor?: string;
  textColor?: string;
  icon?: React.ReactNode;
  interactive?: boolean;
  rightIcon?: React.ReactNode;
  label?: React.ReactNode;
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
  top: -10,
  left: -13,
};

export const BaseTag = (props: Props) => {
  const {
    fillColor = Colors.Gray10,
    textColor = Colors.Gray900,
    icon,
    interactive = false,
    rightIcon,
    label,
  } = props;
  return (
    <StyledTag $fillColor={fillColor} $interactive={interactive} $textColor={textColor}>
      {icon || null}
      {label !== undefined && label !== null ? (
        <span
          data-tooltip={typeof label === 'string' ? label : undefined}
          data-tooltip-style={JSON.stringify({
            ...BaseTagTooltipStyle,
            backgroundColor: fillColor,
            color: textColor,
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
  > ${IconWrapper}:first-child {
    margin-right: 4px;
    margin-left: -4px;
  }

  > ${IconWrapper}:last-child {
    margin-left: 4px;
    margin-right: -4px;
  }

  > ${IconWrapper}:first-child:last-child {
    margin: 0 -4px;
  }
`;
