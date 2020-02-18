import React from "react";
import * as R from "ramda";
import { connectSearchBox } from "react-instantsearch-dom";

const omitNonInputProps = R.omit([
  "createURL",
  "isSearchStalled",
  "currentRefinement",
  "indexContextValue"
]);

export default connectSearchBox(({ refine, focus, collapse, ...rest }) => {
  return (
    <input
      focus={focus ? "true" : "false"}
      collapse={collapse ? "true" : "false"}
      type="text"
      placeholder="Search the docs (press / to focus)"
      aria-label="Search"
      onChange={e => refine(e.target.value)}
      {...omitNonInputProps(rest)}
    />
  );
});
