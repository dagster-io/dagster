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
import { Highlight } from "react-instantsearch-dom";

const client = algoliasearch(
  process.env.NEXT_PUBLIC_ALGOLIA_APP_ID,
  process.env.NEXT_PUBLIC_ALGOLIA_SEARCH_API_KEY
);

const index = client.initIndex(process.env.NEXT_PUBLIC_ALGOLIA_INDEX_NAME);
// index.setSettings({ attributesToHighlight: ["*"] });

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState([]);
  useEffect(() => {
    const path = window.location.href;
    const urlQuery = decodeURIComponent(path.substring(path.indexOf("=") + 1));

    setQuery(urlQuery);
    index.search(urlQuery, { hitsPerPage: 50 }).then(({ hits }) => {
      console.log(hits);
      setHits(hits);
    });
  }, []);

  const router = useRouter();

  // If the page is not yet generated, this shimmer/skeleton will be displayed
  // initially until getStaticProps() finishes running
  if (router.isFallback) {
    return <Shimmer />;
  }

  function parsedLevel(name) {
    if (name == "Title" || name == null) {
      return "";
    }
    return name;
  }

  function renderHit(hit) {
    const hierarchy = hit._highlightResult.hierarchy_camel[0];
    let highlightedLevel = "";
    for (let key in hierarchy) {
      if (hierarchy[key].matchedWords.length > 0) {
        highlightedLevel = key;
        break;
      }
    }

    const lvl0 = parsedLevel(hit.hierarchy.lvl0);
    const lvl1 = parsedLevel(hit.hierarchy.lvl1);
    const lvl2 = parsedLevel(hit.hierarchy.lvl2);

    const page = `${lvl0} ${lvl1 ? ">" : ""} ${lvl1} ${
      lvl2 ? ">" : ""
    } ${lvl2}`;

    // let element = document.create
    return <Highlight hit={hit} attribute="name" />;
  }

  function onChange(e) {
    setQuery(e.target.value);
    index.search(query, { hitsPerPage: 50 }).then(({ hits }) => {
      setHits(hits);
    });
  }

  return (
    <div>
      <input type="text" value={query} onChange={onChange} />
      {hits.map((hit) => {
        return renderHit(hit);
      })}
    </div>
  );
}
