/** @jsx jsx */
import { jsx } from "theme-ui";

import * as styles from "./styles";
import { DetailedHTMLProps, LiHTMLAttributes } from "react";

type ListProps = DetailedHTMLProps<
  LiHTMLAttributes<HTMLLIElement>,
  HTMLLIElement
>;

export const List: React.FC<ListProps> = ({ children, ...props }) => {
  return (
    <li sx={styles.wrapper} {...props}>
      {children}
    </li>
  );
};
