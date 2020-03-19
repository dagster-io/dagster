/** @jsx jsx */
import { jsx, Styled, SxProps } from "theme-ui";
import { HTMLAttributes } from "react";

export const Code: React.FC<HTMLAttributes<HTMLElement> & SxProps> = props => {
  return <Styled.code {...props} />;
};
