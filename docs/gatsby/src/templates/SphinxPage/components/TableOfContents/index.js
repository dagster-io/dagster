/** @jsx jsx */
import { jsx } from "theme-ui";
import { useRef } from "react";
import { FileText } from "react-feather";
import Sticky from "react-stickynode";
import useClickAway from "react-use/lib/useClickAway";
import useKeyPressEvent from "react-use/lib/useKeyPressEvent";

import * as styles from "./styles";

export const TableOfContents = ({ children, isMobile, opened, onClose }) => {
  const ref = useRef(null);
  const content = (
    <div ref={ref} sx={styles.wrapper(isMobile)} onClick={onClose}>
      <Sticky enabled={!isMobile} top={30}>
        <h2 sx={styles.title}>
          <FileText sx={styles.icon} size={14} />
          Contents
        </h2>
        {children}
      </Sticky>
    </div>
  );

  useKeyPressEvent("Escape", onClose);
  useClickAway(ref, ev => {
    if (ev.target.id !== "btnOpenToc") onClose();
  });

  return !isMobile ? (
    content
  ) : (
    <div sx={styles.mobileWrapper(opened)}>{content}</div>
  );
};
