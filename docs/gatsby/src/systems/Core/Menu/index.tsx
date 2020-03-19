/** @jsx jsx */
import { jsx } from "theme-ui";

import * as styles from "./styles";
import { DetailedHTMLProps, HTMLAttributes } from "react";

type MenuProps = DetailedHTMLProps<
  HTMLAttributes<HTMLDivElement>,
  HTMLDivElement
> & {
  gap?: number;
  vertical?: boolean;
};

export const Menu: React.FC<MenuProps> = ({
  children,
  gap = 3,
  vertical,
  ...props
}) => {
  return (
    <div sx={styles.wrapper(gap, !!vertical)} {...props}>
      {children}
    </div>
  );
};
