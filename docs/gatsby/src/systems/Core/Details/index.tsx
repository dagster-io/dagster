/** @jsx jsx */
import { jsx } from "theme-ui";

import * as styles from "./styles";
import { DetailedHTMLProps, HTMLAttributes } from "react";

type DetailsProps = DetailedHTMLProps<
  HTMLAttributes<HTMLDListElement>,
  HTMLDListElement
>;

export const Details: React.FC<DetailsProps> = ({ children, ...props }) => {
  return (
    <dl sx={styles.wrapper} {...props}>
      {children}
    </dl>
  );
};
