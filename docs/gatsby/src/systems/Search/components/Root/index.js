/** @jsx jsx */
import { jsx } from "theme-ui";
import * as styles from "./styles";

export default function({ children }) {
  return <div sx={styles.wrapper}>{children}</div>;
}
