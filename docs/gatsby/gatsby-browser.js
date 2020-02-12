import "highlight.js/styles/github.css";
import * as React from "react";

import { VersionProvider } from "./src/systems/Version";

export const wrapRootElement = ({ element }) => {
  return <VersionProvider>{element}</VersionProvider>;
};
