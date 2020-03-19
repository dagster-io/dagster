/** @jsx jsx */
import { jsx, SxProps } from "theme-ui";

import * as styles from "./styles";

// TODO: Narrow down this component possible tags, in it's current form this can be anything.
export const Heading: React.FC<SxProps & { tagName: any }> = ({
  tagName: Component,
  ...props
}) => {
  return <Component sx={styles.wrapper(Component)} {...props} />;
};
