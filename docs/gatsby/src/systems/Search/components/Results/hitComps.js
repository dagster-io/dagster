import React from 'react'
import { Highlight } from 'react-instantsearch-dom'
import { Link } from 'gatsby'

export const PageHit = (clickHandler, version) => ({ hit }) => (
  <div>
    <Link to={`/${version}/${hit.slug}`} onClick={clickHandler}>
      <h4>
        <Highlight attribute="title" hit={hit} tagName="mark" />
      </h4>
    </Link>
  </div>
)

export const ModuleHit = (clickHandler, version) => ({ hit }) => (
  <div>
    <Link to={`/${version}/${hit.slug}`} onClick={clickHandler}>
      <h4>
        <Highlight attribute="title" hit={hit} tagName="mark" />
      </h4>
    </Link>
  </div>
)
