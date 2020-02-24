import React from "react";
import { Highlight, Snippet } from "react-instantsearch-dom";
import { Link } from "gatsby";

export const PageHit = (clickHandler, version) => ({ hit }) => (
  <div>
    <Link to={`/${version}/${hit.slug}`} onClick={clickHandler}>
      <h4>
        <Highlight attribute="title" hit={hit} tagName="mark" />
      </h4>
      <Snippet attribute="markdown" tagName="mark" hit={hit} />
    </Link>
  </div>
);

export const ModuleHit = (clickHandler, version) => ({ hit }) => {
  return (
    <div>
      <Link to={`/${version}/${hit.slug}`} onClick={clickHandler}>
        <h4>{hit.title}</h4>
        <Snippet attribute="markdown" tagName="mark" hit={hit} />
      </Link>
    </div>
  );
};
