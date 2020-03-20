/** @jsx jsx */
import { jsx } from "theme-ui";
import * as styles from "./styles";

const Root: React.FC = ({ children }) => {
  return <div sx={styles.wrapper}>{children}</div>;
};

export default Root;
