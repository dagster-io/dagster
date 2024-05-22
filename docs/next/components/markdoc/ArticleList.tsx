import {unpackText} from 'util/unpackText';

import NextLink from 'next/link';

import Link from '../Link';

export const ArticleList = ({children}) => {
  return (
    <div className="category-container">
      <div className="category-inner-container">
        <ul
          style={{
            columnCount: 2,
            columnGap: '20px',
            padding: 0,
            margin: 0,
          }}
        >
          {unpackText(children)}
        </ul>
      </div>
    </div>
  );
};

export const ArticleListItem = ({title, href}) => {
  return (
    <li
      style={{
        marginTop: 0,
      }}
    >
      {href.startsWith('http') ? (
        <NextLink href={href} legacyBehavior>
          {title}
        </NextLink>
      ) : (
        <Link href={href}>{title}</Link>
      )}
    </li>
  );
};
