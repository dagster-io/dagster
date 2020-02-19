/** @jsx jsx */
import { jsx } from "theme-ui";
import { useRef, useEffect, useState } from "react";

import { useVersion } from "systems/Version";
import { Link as BaseLink } from "systems/Core";

import { isToctreeLi } from "../List";
import * as styles from "./styles";

export const isSidebarLink = node => {
  const parent = node.parentNode;
  return (
    node.tagName === "a" &&
    parent.tagName === "li" &&
    parent.attrs &&
    parent.attrs.some(isToctreeLi)
  );
};

const getLinkId = path => {
  const found = path.match(/(\w+)\//);
  const link = found ? found[1] : path;
  return link.startsWith("/") ? link.slice(1, Infinity) : link;
};

export const Link = props => {
  const { href, children } = props;
  const { version } = useVersion();
  const [isPartiallyActive, setPartiallyActive] = useState(true);

  const ref = useRef(null);
  const id = getLinkId(href);
  const commonProps = { id, sx: styles.link };

  useEffect(() => {
    if (ref && ref.current) {
      const parent = ref.current.parentNode;
      setPartiallyActive(!parent.classList.contains("toctree-l2"));
    }
  }, []);

  return href.startsWith("http") ? (
    <a
      {...commonProps}
      alt={id}
      href={href}
      rel="noreferrer noopener"
      target="_blank"
    >
      {children}
    </a>
  ) : (
    // eslint-disable-next-line jsx-a11y/anchor-is-valid
    <BaseLink
      {...commonProps}
      ref={ref}
      to={`/${version.current}/${href}`}
      partiallyActive={isPartiallyActive}
    >
      {children}
    </BaseLink>
  );
};
