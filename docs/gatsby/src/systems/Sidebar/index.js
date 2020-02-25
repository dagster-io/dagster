/** @jsx jsx */
import { jsx } from "theme-ui";
import { forwardRef } from "react";
import { useMachine } from "@xstate/react";
import { useStaticQuery, graphql } from "gatsby";
import useWindowSize from "react-use/lib/useWindowSize";
import { useEffect } from "react";

import { Link, Menu } from "systems/Core";
import { ReactParser, isText } from "systems/ReactParser";
import { useLocalStorage } from "utils/localStorage";
import { VersionSelector } from "systems/Version/components/VersionSelector";

import { activeMenuMachine } from "./machines/activeMenu";
import { isSidebarList, List as SidebarList } from "./components/List";
import { isSidebarLink, Link as SidebarLink } from "./components/Link";
import { useElement } from "../ReactParser/hooks/useElement";
import * as styles from "./styles";

export const renderElements = () => (renderedNodes, node, idx, _nodes) => {
  const { tagName: Component, nodeName, value = [] } = node;
  const { props, children } = useElement(node, renderElements);

  if (isText(node)) {
    renderedNodes.push(node.value);
  } else if (nodeName === "#text") {
    renderedNodes.push(value);
  } else if (!Component) {
    renderedNodes.push(null);
  } else if (isSidebarList(node)) {
    renderedNodes.push(
      <SidebarList key={idx} {...props}>
        {children}
      </SidebarList>
    );
  } else if (isSidebarLink(node)) {
    renderedNodes.push(
      <SidebarLink key={idx} {...props}>
        {children}
      </SidebarLink>
    );
  } else if (Component === "a") {
    renderedNodes.push(
      <Link key={idx} {...props}>
        {children}
      </Link>
    );
  } else {
    renderedNodes.push(
      <Component key={idx} {...props}>
        {children}
      </Component>
    );
  }

  return renderedNodes;
};

export const Sidebar = forwardRef(({ opened, location }, ref) => {
  const { width } = useWindowSize();
  const data = useStaticQuery(graphql`
    query IndexPage {
      page: sphinxPage(current_page_name: { eq: "index" }) {
        parsed
      }
    }
  `);

  const storage = useLocalStorage("activeMenuTop");
  const [state, send] = useMachine(
    activeMenuMachine.withContext({
      storage,
      top: storage ? storage.get() : 0
    })
  );

  const { top, active } = state.context;

  useEffect(() => {
    send("FIND_REFERENCE", { location: location });
  }, [location, send]);

  return (
    <div ref={ref} sx={styles.wrapper(opened && width < 1024)}>
      <div sx={styles.content}>
        <Menu vertical sx={styles.menu}>
          {Boolean(top) && <span sx={styles.active(active, top)} />}
          <ReactParser
            tree={data.page.parsed}
            renderElements={renderElements}
          />
          <h6 class="version-wrapper">
            Version: <VersionSelector />
          </h6>
        </Menu>
      </div>
    </div>
  );
});
