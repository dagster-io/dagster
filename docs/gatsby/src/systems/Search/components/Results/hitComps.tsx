import React from "react";
import { Highlight, Snippet } from "react-instantsearch-dom";
import { Link } from "gatsby";

type OnClickEventHandler = (
  event: React.MouseEvent<HTMLAnchorElement, MouseEvent>
) => void;

type Hit = {
  hit: {
    slug?: string;
    title?: string;
  };
};

export const PageHit = (
  clickHandler: OnClickEventHandler,
  version: string
) => ({ hit }: Hit) => (
  <div>
    <Link to={`/${version}/${hit.slug}`} onClick={clickHandler}>
      <h4>
        <Highlight attribute="title" hit={hit} tagName="mark" />
      </h4>
      <Snippet attribute="markdown" tagName="mark" hit={hit} />
    </Link>
  </div>
);

export const ModuleHit = (
  clickHandler: OnClickEventHandler,
  version: string
) => ({ hit }: Hit) => (
  <div>
    <Link to={`/${version}/${hit.slug}`} onClick={clickHandler}>
      <h4>{hit.title}</h4>
      <Snippet attribute="markdown" tagName="mark" hit={hit} />
    </Link>
  </div>
);
