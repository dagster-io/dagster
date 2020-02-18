/** @jsx jsx */
import { jsx } from "theme-ui";
import React, { useState, useEffect } from "react";
import { Search as SearchIcon, XCircle } from "react-feather";
import { InstantSearch } from "react-instantsearch-dom";
import useWindowSize from "react-use/lib/useWindowSize";
import useClickAway from "react-use/lib/useClickAway";
import algoliasearch from "algoliasearch/lite";

import * as styles from "./styles";
import Root from "./components/Root";
import Input from "./components/Input";
import Results from "./components/Results";

export const Search = React.forwardRef((props, ref) => {
  const { showing, onClick, indices } = props;
  const { width } = useWindowSize();
  const [query, setQuery] = useState("");
  const [focus, setFocus] = useState(false);

  const searchClient = algoliasearch(
    process.env.GATSBY_ALGOLIA_APP_ID,
    process.env.GATSBY_ALGOLIA_SEARCH_KEY
  );

  const handleClickSearchIcon = () => {
    onClick();
  };

  useClickAway(ref, () => {
    setFocus(false);
  });

  return (
    <InstantSearch
      searchClient={searchClient}
      indexName={indices[0].name}
      onSearchStateChange={({ query }) => setQuery(query)}
      root={{ Root, props: { ref } }}
    >
      {!showing && width < 1024 && (
        <div ref={ref} sx={styles.searchMobile}>
          <SearchIcon size={25} onClick={handleClickSearchIcon} />
        </div>
      )}
      {(showing || width >= 1024) && (
        <div ref={ref} sx={styles.search}>
          <SearchIcon size={25} onClick={handleClickSearchIcon} />
          <Input
            onFocus={() => setFocus(true)}
            {...{ collapse: true, focus }}
          />
          {showing && width < 1024 && <XCircle onClick={onClick} />}
          <Results
            indices={indices}
            showing={query && query.length > 0 && focus}
            onClose={() => setFocus(false)}
          />
        </div>
      )}
    </InstantSearch>
  );
});
