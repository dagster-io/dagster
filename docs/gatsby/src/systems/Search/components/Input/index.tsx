import React from "react";
import * as R from "ramda";
import { connectSearchBox } from "react-instantsearch-dom";
import { SearchBoxProvided } from "react-instantsearch-core";

const omitNonInputProps = R.omit([
  "createURL",
  "isSearchStalled",
  "currentRefinement",
  "indexContextValue"
]);

type InputProps = SearchBoxProvided & {
  focus?: boolean;
  collapse?: boolean;
};

// TODO: Handle focus in a different way, focus is not a prop of input.
export default connectSearchBox<InputProps>(
  ({ refine, focus, collapse, ...rest }) => {
    return (
      <input
        // eslint-disable-next-line @typescript-eslint/ban-ts-ignore
        // @ts-ignore
        focus={focus ? "true" : "false"}
        collapse={collapse ? "true" : "false"}
        type="text"
        placeholder="Search the docs (press / to focus)"
        aria-label="Search"
        onChange={e => refine(e.target.value)}
        {...omitNonInputProps(rest)}
      />
    );
  }
);
