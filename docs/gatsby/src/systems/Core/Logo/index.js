/** @jsx jsx */
import { jsx } from "theme-ui";
import { Link } from "gatsby";

import logo from "./logo.png";

export const Logo = props => {
  return (
    <Link to="/">
      <img src={logo} {...props} sx={{ m: 0 }} />
    </Link>
  );
};
