/** @jsx jsx */
import { jsx } from "theme-ui";
import { useRef, useEffect } from "react";

import * as styles from "./styles";
import { TraverseNode } from "systems/Core/CodeSection";

type ToctreeLiInput = {
  name: string;
  value: string;
};

export const isToctreeLi = ({ name, value }: ToctreeLiInput) => {
  return name === "class" && value.startsWith("toctree");
};

export const isSidebarList = (node: TraverseNode) => {
  return node.tagName === "li" && node.attrs.some(isToctreeLi);
};

export const List: React.FC = ({ children, ...props }) => {
  const ref = useRef<HTMLLIElement>(null);

  useEffect(() => {
    if (!ref.current) return;
    const el = ref.current;
    const child = el.childNodes[0] as ChildNode & HTMLElement;

    if (child.classList.contains("active")) {
      el.classList.add("active");
    }
  }, []);

  return (
    <li ref={ref} sx={styles.wrapper} {...props}>
      {children}
    </li>
  );
};
