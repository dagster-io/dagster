/** @jsx jsx */
import { jsx } from "theme-ui";
import { useRef, useEffect } from "react";

import * as styles from "./styles";

export const isToctreeLi = ({ name, value }) => {
  return name === "class" && value.startsWith("toctree");
};

export const isSidebarList = node => {
  return node.tagName === "li" && node.attrs.some(isToctreeLi);
};

export const List = ({ children, ...props }) => {
  const ref = useRef(null);

  useEffect(() => {
    if (!ref.current) return;
    const el = ref.current;
    const child = el.childNodes[0];

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
