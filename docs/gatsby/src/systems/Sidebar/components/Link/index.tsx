/** @jsx jsx */
import { jsx } from "theme-ui";
import { useRef, useEffect, useState } from "react";

import { useVersion } from "systems/Version";
import { Link as BaseLink } from "systems/Core";

import { isToctreeLi } from "../List";
import * as styles from "./styles";
import { TraverseNode } from "systems/Core/CodeSection";

export const isSidebarLink = (node: TraverseNode) => {
  const parent = node.parentNode as TraverseNode;
  return (
    node.tagName === "a" &&
    parent.tagName === "li" &&
    parent.attrs &&
    parent.attrs.some(isToctreeLi)
  );
};

const getLinkId = (path: string) => {
  const found = path.match(/(\w+)\//);
  const link = found ? found[1] : path;
  return link.startsWith("/") ? link.slice(1, Infinity) : link;
};

type LinkProps = {
  href?: string;
};

export const Link: React.FC<LinkProps> = ({ href, children }) => {
  const { version } = useVersion();
  const [isPartiallyActive, setPartiallyActive] = useState(true);

  const ref = useRef(null);
  const id = getLinkId(href!);
  const commonProps = { id, sx: styles.link };

  useEffect(() => {
    if (ref && ref.current) {
      // TODO: Fix this ref type.
      const parent = (ref.current! as any).parentNode;
      setPartiallyActive(!parent.classList.contains("toctree-l2"));
    }
  }, []);

  return href!.startsWith("http") ? (
    <a
      {...commonProps}
      // TODO: Check alt, <a> items don't have alt
      // eslint-disable-next-line @typescript-eslint/ban-ts-ignore
      // @ts-ignore
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
