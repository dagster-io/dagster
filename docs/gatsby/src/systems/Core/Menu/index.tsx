/** @jsx jsx */
import { jsx } from "theme-ui";

import * as styles from "./styles";

type MenuProps = JSX.IntrinsicElements["div"] & {
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
