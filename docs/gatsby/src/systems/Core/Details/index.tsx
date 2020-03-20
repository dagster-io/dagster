/** @jsx jsx */
import { jsx } from "theme-ui";

import * as styles from "./styles";

type DetailsProps = JSX.IntrinsicElements["dl"];

export const Details: React.FC<DetailsProps> = ({ children, ...props }) => {
  return (
    <dl sx={styles.wrapper} {...props}>
      {children}
    </dl>
  );
};
