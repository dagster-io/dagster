import React from "react";

import MDXComponents from "../components/mdx/MDXComponents";
import FeedbackModal from "../components/FeedbackModal";
import { MDXData, UnversionedMDXRenderer } from "../components/mdx/MDXRenderer";

import { GetStaticProps } from "next";
import { MdxRemote } from "next-mdx-remote/types";
import { promises as fs } from "fs";
import generateToc from "mdast-util-toc";
import matter from "gray-matter";
import mdx from "remark-mdx";
import path from "path";
import rehypePlugins from "components/mdx/rehypePlugins";
import remark from "remark";
import renderToString from "next-mdx-remote/render-to-string";
import { useRouter } from "next/router";
import visit from "unist-util-visit";
import { Shimmer } from "components/Shimmer";
import algoliasearch from "algoliasearch";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  Highlight,
  InstantSearch,
  Hits,
  SearchBox,
  Pagination,
} from "react-instantsearch-dom";

const client = algoliasearch(
  process.env.NEXT_PUBLIC_ALGOLIA_APP_ID,
  process.env.NEXT_PUBLIC_ALGOLIA_SEARCH_API_KEY
);

const index = client.initIndex(process.env.NEXT_PUBLIC_ALGOLIA_INDEX_NAME);

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

  const a = document.createElement("a");
  a.href = hit.url;
  const hash = a.hash === "#content-wrapper" ? "" : a.hash;
  let url = `${a.pathname}${hash}`;

  return (
    <a href={url}>
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

export default function SearchPage() {
  // const [query, setQuery] = useState("");
  // const [hits, setHits] = useState([]);
  // useEffect(() => {
  //   const path = window.location.href;
  //   const urlQuery = decodeURIComponent(path.substring(path.indexOf("=") + 1));

  //   setQuery(urlQuery);
  //   index.search(urlQuery, { hitsPerPage: 50 }).then(({ hits }) => {
  //     console.log(hits);
  //     setHits(hits);
  //   });
  // }, []);

  const router = useRouter();

  // If the page is not yet generated, this shimmer/skeleton will be displayed
  // initially until getStaticProps() finishes running
  if (router.isFallback) {
    return <Shimmer />;
  }

  return (
    <div className="w-full py-4">
      <InstantSearch
        searchClient={client}
        indexName={process.env.NEXT_PUBLIC_ALGOLIA_INDEX_NAME}
      >
        <SearchBox />
        <Hits hitComponent={Hit} />
        <Pagination className="mt-5 mb-5" />
      </InstantSearch>
    </div>
  );
}
