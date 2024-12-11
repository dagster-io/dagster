import styled, {css} from 'styled-components';

import {Box} from './Box';
import {Colors} from './Color';

type Colors =
  | string
  | {
      link: string;
      hover?: string;
      active?: string;
    };

type Underline = 'never' | 'always' | 'hover';

type Props = Omit<React.HTMLProps<HTMLButtonElement>, 'color'> & {
  color?: Colors;
  disabled?: boolean;
  underline?: Underline;
  children?: React.ReactNode;
};

const fontColor = (color: Colors) => {
  if (typeof color === 'string') {
    return css`
      color: ${color};
    `;
  }

  const {link, hover, active} = color;
  return css`
    color: ${link};
    ${hover ? `&:hover { color: ${hover}; }` : null}
    ${active ? `&:active { color: ${active}; }` : null}
  `;
};

const textDecoration = (underline: Underline) => {
  switch (underline) {
    case 'always':
      return css`
        text-decoration: underline;
      `;
    case 'hover':
      return css`
        &:hover {
          text-decoration: underline;
          & > ${Box} {
            text-decoration: underline;
          }
        }
      `;
    case 'never':
    default:
      return null;
  }
};

export const ButtonLink = styled(
  ({color: _color, underline: _underline, type: _type, ...rest}: Props) => <button {...rest} />,
)<Props>`
  background: transparent;
  border: 0;
  cursor: pointer;
  font-size: inherit;
  line-height: 1;
  padding: 8px;
  margin: -8px;
  text-align: left;

  &:disabled {
    cursor: default;
    opacity: 0.7;
  }

  &:focus:not(:focus-visible) {
    outline: none;
  }

  transition: 30ms color linear;

  ${({color}) => fontColor(color || Colors.linkDefault())}
  ${({underline}) => textDecoration(underline || 'hover')}
`;
