import * as React from 'react';
import {useRef} from 'react';
import styled, {css} from 'styled-components/macro';

import {Colors} from './Colors';

const DISABLED_COLOR = Colors.Gray300;

type Format = 'check' | 'star' | 'switch';
type Size = 'small' | 'large';

type Props = Omit<
  React.DetailedHTMLProps<React.InputHTMLAttributes<HTMLInputElement>, HTMLInputElement>,
  'size'
> & {
  checked: boolean;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  label?: React.ReactNode;
  indeterminate?: boolean;
  format?: Format;
  fillColor?: string;
  size?: Size;
};

interface IconProps {
  checked: boolean;
  disabled: boolean;
  indeterminate: boolean;
  fillColor: string;
}

const StarIcon: React.FC<IconProps> = ({checked, indeterminate, fillColor, disabled}) => (
  <svg width="24px" height="24px" viewBox="-3 -3 24 24">
    <path
      className="interaction-focus-outline"
      d="M8.99983 14.27L13.1498 16.78C13.9098 17.24 14.8398 16.56 14.6398 15.7L13.5398 10.98L17.2098 7.80001C17.8798 7.22001 17.5198 6.12001 16.6398 6.05001L11.8098 5.64001L9.91983 1.18001C9.57983 0.37001 8.41983 0.37001 8.07983 1.18001L6.18983 5.63001L1.35983 6.04001C0.479829 6.11001 0.119828 7.21001 0.789828 7.79001L4.45983 10.97L3.35983 15.69C3.15983 16.55 4.08983 17.23 4.84983 16.77L8.99983 14.27Z"
      fill={Colors.White}
    />
    <path
      d="M16.65 6.04L11.81 5.62L9.92 1.17C9.58 0.36 8.42 0.36 8.08 1.17L6.19 5.63L1.36 6.04C0.48 6.11 0.12 7.21 0.79 7.79L4.46 10.97L3.36 15.69C3.16 16.55 4.09 17.23 4.85 16.77L9 14.27L13.15 16.78C13.91 17.24 14.84 16.56 14.64 15.7L13.54 10.97L17.21 7.79C17.88 7.21 17.53 6.11 16.65 6.04ZM9 12.4L5.24 14.67L6.24 10.39L2.92 7.51L7.3 7.13L9 3.1L10.71 7.14L15.09 7.52L11.77 10.4L12.77 14.68L9 12.4Z"
      className="interaction-darken"
      fill={Colors.Gray300}
      style={{opacity: disabled ? 0.6 : 1}}
    />
    {indeterminate && (
      <path
        d="M11.6490126,5.26286597 L11.8098,5.64001 L16.6398,6.05001 C17.5198,6.12001 17.8798,7.22001 17.2098,7.80001 L17.2098,7.80001 L13.5398,10.98 L14.6398,15.7 C14.8398,16.56 13.9098,17.24 13.1498,16.78 L13.1498,16.78 L8.99983,14.27 L4.84983,16.77 C4.49121528,16.9870563 4.09474951,16.9502879 3.79701262,16.7605538 L11.6490126,5.26286597 Z"
        className="interaction-darken"
        fill={fillColor}
        style={{opacity: disabled ? 0.6 : 1}}
      />
    )}
    <path
      d="M8.99983 14.27L13.1498 16.78C13.9098 17.24 14.8398 16.56 14.6398 15.7L13.5398 10.98L17.2098 7.80001C17.8798 7.22001 17.5198 6.12001 16.6398 6.05001L11.8098 5.64001L9.91983 1.18001C9.57983 0.37001 8.41983 0.37001 8.07983 1.18001L6.18983 5.63001L1.35983 6.04001C0.479829 6.11001 0.119828 7.21001 0.789828 7.79001L4.45983 10.97L3.35983 15.69C3.15983 16.55 4.08983 17.23 4.84983 16.77L8.99983 14.27Z"
      className="interaction-darken"
      fill={fillColor}
      style={{
        transformOrigin: '9px 9px',
        transform: !indeterminate && checked ? 'scale(1,1)' : 'scale(0,0)',
        transition: 'transform 80ms linear',
        opacity: disabled ? 0.4 : 1,
      }}
    />
  </svg>
);

const SwitchIcon: React.FC<IconProps> = ({checked, indeterminate, fillColor, disabled}) => (
  <svg width="36px" height="24px" viewBox="-3 -3 42 28">
    <defs>
      <linearGradient x1="50%" y1="0%" x2="50%" y2="100%" id="innerShadow">
        <stop stopColor="#000" stopOpacity="0.2" offset="0%" />
        <stop stopColor="#000" stopOpacity="0.12" offset="15%" />
        <stop stopColor="#000" stopOpacity="0.06" offset="40%" />
        <stop stopColor="#000" stopOpacity="0" offset="100%" />
      </linearGradient>
    </defs>
    <rect
      id="bg"
      x="0"
      y="0"
      width="36"
      height="22"
      rx="11"
      fill={checked && !indeterminate ? fillColor : Colors.Gray400}
      style={{
        transition: 'fill 100ms linear',
        opacity: disabled && checked && !indeterminate ? 0.6 : 1,
      }}
      className="interaction-darken interaction-focus-outline"
    />
    {!disabled && <rect x="0" y="0" width="36" height="22" rx="11" fill="url(#innerShadow)" />}
    <rect
      id="handle"
      style={{transition: 'x 100ms linear'}}
      x={indeterminate ? '8' : checked ? '15' : '1'}
      y="1"
      width="20"
      height="20"
      rx="10"
      fill={disabled ? Colors.Gray200 : Colors.White}
    />
  </svg>
);

const CheckIcon: React.FC<IconProps> = ({checked, indeterminate, fillColor, disabled}) => (
  <svg width="24px" height="24px" viewBox="-3 -3 24 24">
    <path
      d="M16,0 C17.1,0 18,0.9 18,2 L18,2 L18,16 C18,17.1 17.1,18 16,18 L16,18 L2,18 C0.9,18 0,17.1 0,16 L0,16 L0,2 C0,0.9 0.9,0 2,0 L2,0 Z"
      id="Background"
      className=" interaction-focus-outline"
      style={{transition: 'fill 100ms linear'}}
      fill={Colors.White}
    />
    <path
      id="Border"
      className="interaction-darken"
      d="M15 16H3C2.45 16 2 15.55 2 15V3C2 2.45 2.45 2 3 2H15C15.55 2 16 2.45 16 3V15C16 15.55 15.55 16 15 16ZM16 0H2C0.9 0 0 0.9 0 2V16C0 17.1 0.9 18 2 18H16C17.1 18 18 17.1 18 16V2C18 0.9 17.1 0 16 0Z"
      fill={Colors.Gray300}
      style={{opacity: disabled ? (checked ? 0.4 : 0.6) : 1}}
    />
    <path
      d="M16,0 C17.1,0 18,0.9 18,2 L18,2 L18,16 C18,17.1 17.1,18 16,18 L16,18 L2,18 C0.9,18 0,17.1 0,16 L0,16 L0,2 C0,0.9 0.9,0 2,0 L2,0 Z"
      id="Fill"
      className="interaction-darken"
      style={{transition: 'fill 100ms linear', opacity: disabled ? 0.6 : 1}}
      fill={checked || indeterminate ? fillColor : 'transparent'}
    />
    <polyline
      id="Check"
      fill="none"
      stroke={Colors.White}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeDasharray="16"
      style={{
        transition: 'stroke-dashoffset 100ms linear',
        transitionDelay: !(checked && !indeterminate) ? '80ms' : '0',
      }}
      strokeDashoffset={checked && !indeterminate ? '0' : '16'}
      points="3.5 9 7 12.5 14.5 5.0"
    />
    <line
      id="Indeterminate"
      x1="5"
      y1="9"
      x2="13"
      y2="9"
      style={{
        transition: 'stroke-dashoffset 100ms linear',
        transitionDelay: !indeterminate ? '80ms' : '0',
      }}
      stroke={Colors.White}
      strokeWidth="2"
      strokeDasharray="8"
      strokeLinecap="round"
      strokeDashoffset={indeterminate ? '0' : '8'}
    />
  </svg>
);

let counter = 0;
const uniqueId = () => `checkbox-${counter++}`;

const Base = ({
  id,
  checked,
  label,
  className,
  format = 'check',
  disabled = false,
  indeterminate = false,
  fillColor = Colors.Blue500,
  children, // not passed to input
  size,
  ...rest
}: Props) => {
  const uid = useRef(id || uniqueId());
  const Component: React.FC<IconProps> = {star: StarIcon, check: CheckIcon, switch: SwitchIcon}[
    format
  ];

  return (
    <label htmlFor={uid.current} className={className}>
      <input
        {...rest}
        type="checkbox"
        id={uid.current}
        tabIndex={0}
        checked={checked}
        disabled={disabled}
      />
      <Component
        disabled={disabled}
        checked={checked}
        indeterminate={indeterminate}
        fillColor={fillColor}
      />
      {label}
    </label>
  );
};

const svgStyle = (values: {size?: Size; format?: Format}) => {
  const {size = 'large', format = 'check'} = values;

  if (size === 'large') {
    return css`
      margin: -3px;
    `;
  }

  if (format === 'switch') {
    return css`
      margin: -3px -9px;
      transform: scale(0.5);
    `;
  }

  return css`
    margin: -3px -6px;
    transform: scale(0.75);
  `;
};

export const Checkbox = styled(Base)`
  display: inline-flex;
  position: relative;
  user-select: none;
  align-items: flex-start;
  color: ${({disabled}) => (disabled ? DISABLED_COLOR : Colors.Gray900)};
  cursor: pointer;
  gap: 8px;

  svg {
    flex-shrink: 0;
    ${svgStyle}
  }

  input[type='checkbox'] {
    position: absolute;
    cursor: pointer;
    opacity: 0;
    height: 0;
    width: 0;
  }

  input:focus + svg {
    .interaction-focus-outline {
      stroke: rgba(58, 151, 212, 0.6);
      stroke-width: 6px;
      paint-order: stroke fill;
    }
  }
  /* Focus outline only when using keyboard, not when focusing via mouse,
     if focus-visible is supported and this rule is understood. */
  input:focus:not(input:focus-visible) + svg {
    .interaction-focus-outline {
      stroke-width: 0;
    }
  }

  ${({disabled}) =>
    !disabled &&
    `
    svg:hover {
      filter: drop-shadow(0 0 5px rgba(0, 0, 0, 0.12));

      &.interaction-darken,
      .interaction-darken {
        filter: brightness(0.8);
      }
    }
  `}
`;
