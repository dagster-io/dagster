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

const client = algoliasearch(
  process.env.NEXT_PUBLIC_ALGOLIA_APP_ID,
  process.env.NEXT_PUBLIC_ALGOLIA_SEARCH_API_KEY
);

const index = client.initIndex(process.env.NEXT_PUBLIC_ALGOLIA_INDEX_NAME);

export default function SearchPage() {
  const [query, setQuery] = useState(null);
  useEffect(() => {
    const path = window.location.href;

    if (path.includes("?")) {
      setQuery(decodeURIComponent(path.substring(path.indexOf("?") + 1)));
    }
  });
  const router = useRouter();

  console.log(query);

  // If the page is not yet generated, this shimmer/skeleton will be displayed
  // initially until getStaticProps() finishes running
  if (router.isFallback) {
    return <Shimmer />;
  }

  index.search(query).then(({ hits }) => {
    console.log(hits);
  });
  return <div>foo</div>;
}
