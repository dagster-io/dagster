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

const components: MdxRemote.Components = MDXComponents;

enum PageType {
  MDX = "MDX",
}

type Props = {
  type: PageType.MDX;
  data: MDXData;
};

const client = algoliasearch(
  process.env.NEXT_PUBLIC_ALGOLIA_APP_ID,
  process.env.NEXT_PUBLIC_ALGOLIA_SEARCH_API_KEY
);

const index = client.initIndex(process.env.NEXT_PUBLIC_ALGOLIA_INDEX_NAME);

export const SearchPage = (query) => {
  index.search(query).then(({ hits }) => {
    console.log(hits);
  });
  return <div>foo</div>;
};

export default function MdxPage(props: Props) {
  const router = useRouter();

  // If the page is not yet generated, this shimmer/skeleton will be displayed
  // initially until getStaticProps() finishes running
  if (router.isFallback) {
    return <Shimmer />;
  }

  return <>yay</>;
}
