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

interface Props extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'color'> {
  color?: Colors;
  underline?: Underline;
}

export const ButtonLink = styled(({color: _color, underline: _underline, ...rest}: Props) => (
  <button {...rest} />
))`
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
