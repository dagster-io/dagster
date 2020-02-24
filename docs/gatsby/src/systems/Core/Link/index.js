/** @jsx jsx */
import { Styled, jsx } from "theme-ui";
import { forwardRef } from "react";
import { Link as BaseLink } from "gatsby";
import { Location } from "@reach/router";
import path from "path-browserify";

import * as styles from "./styles";

const parseHrefLink = href => {
  const link = href.endsWith(".html") ? href.slice(0, href.length - 5) : href;
  return link.startsWith("/") ? `..${link}` : link;
};

export const Link = forwardRef(({ href, to, isNav, ...props }, ref) => {
  const isExternal = href && href.startsWith("http");
  return isExternal ? (
    // eslint-disable-next-line jsx-a11y/anchor-has-content
    <Styled.a href={href} sx={styles.wrapper} {...props} />
  ) : (
    <Location>
      {({ location }) => {
        const toLink = isNav ? path.resolve(location.pathname, to) : to;
        if (isNav && toLink === "/") return null;

        return (
          <BaseLink
            ref={ref}
            partiallyActive
            activeClassName="active"
            sx={styles.wrapper}
            to={
              href && !isExternal
                ? `${path.resolve(location.pathname, parseHrefLink(href))}`
                : `/${toLink}`
            }
            {...props}
          />
        );
      }}
    </Location>
  );
});
