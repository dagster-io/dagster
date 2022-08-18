import React from "react";
import algoliasearch from "algoliasearch";
import {
  Highlight,
  InstantSearch,
  Hits,
  SearchBox,
  Pagination,
} from "react-instantsearch-dom";
import { findResultsState } from "react-instantsearch-dom/server";

const searchClient = algoliasearch(
  process.env.NEXT_PUBLIC_ALGOLIA_APP_ID,
  process.env.NEXT_PUBLIC_ALGOLIA_SEARCH_API_KEY
);
const indexName = process.env.NEXT_PUBLIC_ALGOLIA_INDEX_NAME;

function HitComponent(hit) {
  function parsedLevel(name) {
    if (name == "Title" || name == null) {
      return "";
    }
    return name;
  }

  const lvl0 = parsedLevel(hit.hierarchy.lvl0);
  const lvl1 = parsedLevel(hit.hierarchy.lvl1);
  const lvl2 = parsedLevel(hit.hierarchy.lvl2);

  let highlightAttr = hit.content != null ? "content" : null;

  let section = null;

  for (const [key, val] of Object.entries(hit.hierarchy)) {
    if (val != "Title" && val != null) {
      section = `hierarchy.${key}`;
    }
  }

  const path = `${lvl0} ${lvl1 ? "|" : ""} ${lvl1} ${lvl2 ? "|" : ""} ${lvl2}`;

  const hitUrl = new URL(hit.url);
  const hash = hitUrl.hash === "#content-wrapper" ? "" : hitUrl.hash;
  const pathUrl = `${hitUrl.pathname}${hash}`;

  return (
    <a href={pathUrl}>
      <div className="SearchHit">
        <Highlight hit={hit} attribute={section} tagName="mark" />
        <p className="SearchPath">{path}</p>
        {highlightAttr && (
          <Highlight
            hit={hit}
            attribute={highlightAttr}
            tagName="mark"
            className="SearchSnippet"
          />
        )}
      </div>
    </a>
  );
}

const Hit = ({ hit }) => HitComponent(hit);

const SearchPage = ({ query, resultsState, widgetsCollector }) => {
  return (
    <div className="w-full py-4">
      <InstantSearch
        searchState={query}
        searchClient={searchClient}
        resultsState={resultsState}
        indexName={indexName}
        widgetsCollector={widgetsCollector}
      >
        <SearchBox />
        <Hits hitComponent={Hit} />
        <Pagination className="mt-5 mb-5" />
      </InstantSearch>
    </div>
  );
};

SearchPage.getInitialProps = async ({ query }) => {
  const resultsState = await findResultsState(SearchPage, {
    searchClient: searchClient,
    searchState: query,
    indexName: indexName,
  });

  return { query, resultsState };
};

export default SearchPage;
