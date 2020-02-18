/** @jsx jsx */
import { jsx } from "theme-ui";
import React, { useState } from "react";
import { Search as SearchIcon } from "react-feather";
import { InstantSearch } from "react-instantsearch-dom";
import useClickAway from "react-use/lib/useClickAway";
import algoliasearch from "algoliasearch/lite";

import * as styles from "./styles";
import Root from "./components/Root";
import Input from "./components/Input";
import Results from "./components/Results";

export const Search = React.forwardRef((props, ref) => {
  const { showing, onClick, indices } = props;
  const [query, setQuery] = useState("");
  const [focus, setFocus] = useState(false);

  const searchClient = algoliasearch(
    process.env.GATSBY_ALGOLIA_APP_ID,
    process.env.GATSBY_ALGOLIA_SEARCH_KEY
  );

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
      <div ref={ref} sx={styles.search}>
        <SearchIcon size={25} onClick={() => onClick()} />
        <Input onFocus={() => setFocus(true)} {...{ collapse: true, focus }} />
        <Results
          indices={indices}
          showing={query && query.length > 0 && focus}
          onClose={() => setFocus(false)}
        />
      </div>
    </InstantSearch>
  );
});
