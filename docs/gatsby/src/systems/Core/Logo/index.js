/** @jsx jsx */
import { jsx } from "theme-ui";

import logo from "./logo.png";

export const Logo = props => {
  return <img src={logo} {...props} sx={{ m: 0 }} />;
};
