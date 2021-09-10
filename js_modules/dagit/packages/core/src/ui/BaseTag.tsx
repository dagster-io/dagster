import * as React from 'react';
import styled from 'styled-components/macro';

import {ColorsWIP} from './Colors';
import {IconWrapper} from './Icon';

interface Props {
  fillColor?: string;
  iconColor?: string;
  textColor?: string;
  icon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  label?: React.ReactNode;
}

export const BaseTag = (props: Props) => {
  const {
    fillColor = ColorsWIP.Gray10,
    iconColor = ColorsWIP.Gray900,
    textColor = ColorsWIP.Gray900,
    icon,
    rightIcon,
    label,
  } = props;
  return (
    <StyledTag $fillColor={fillColor} $textColor={textColor} $iconColor={iconColor}>
      {icon || null}
      {label ? <span>{label}</span> : null}
      {rightIcon || null}
    </StyledTag>
  );
};

interface StyledTagProps {
  $fillColor: string;
  $textColor: string;
  $iconColor: string;
}

const StyledTag = styled.div<StyledTagProps>`
  background-color: ${({$fillColor}) => $fillColor};
  border-radius: 8px;
  color: ${({$textColor}) => $textColor};
  cursor: default;
  display: inline-flex;
  flex-direction: row;
  font-size: 12px;
  line-height: 16px;
  align-items: center;
  padding: 4px 8px;
  user-select: none;

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

  > ${IconWrapper} {
    color: ${({$iconColor}) => $iconColor};
  }
`;

// export const PrettyTag = styled(Tag)`
//   &.bp3-tag {
//     background-color: #f5f4f2;
//     border-radius: 8px;
//     color: #524e48;
//     font-size: 12px;
//     padding: 4px 8px;
//     user-select: none;
//   }

//   &.bp3-tag.bp3-large {
//     border-radius: 16px;
//     padding: 8px 16px;
//   }

//   &.bp3-tag.bp3-intent-primary {
//     background-color: #edecfc;
//     color: #0e0ca7;
//   }

//   &.bp3-tag.bp3-intent-success {
//     background-color: #edf9f3;
//     color: #12754b;
//   }

//   &.bp3-tag.bp3-intent-danger {
//     background-color: #fceeed;
//     color: #a50906;
//   }

//   &.bp3-tag.bp3-intent-warning {
//     background-color: #fff6e6;
//     color: #a55802;
//   }

//   & .MuiSvgIcon-root {
//     font-size: 0.9rem;
//   }

//   &.bp3-tag > *:not(:last-child) {
//     margin-right: 6px;
//   }
// `;
