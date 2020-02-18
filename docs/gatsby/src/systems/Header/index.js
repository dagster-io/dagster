/** @jsx jsx */
import { jsx } from "theme-ui";
import { forwardRef, useEffect, useRef, useState } from "react";
import useWindowSize from "react-use/lib/useWindowSize";

import { ExternalLink, Menu, Logo } from "systems/Core";
import { Search } from "systems/Search";

import githubIcon from "./images/github-icon.svg";
import slackIcon from "./images/slack-icon.svg";
import stackOverflowIcon from "./images/stack-overflow-icon.svg";

import { MenuIcon } from "./components/MenuIcon";
import * as styles from "./styles";

const indices = [
  { name: `Pages`, title: `Pages`, hitComp: `PageHit` },
  { name: `Modules`, title: `Modules`, hitComp: `ModuleHit` }
];

export const Header = forwardRef(({ onMenuClick, sidebarOpened }, ref) => {
  const searchRef = useRef(null);
  const { width } = useWindowSize();
  const [showingSearch, setShowingSearch] = useState(width >= 1024);

  function handleToggleSearch() {
    setShowingSearch(s => !s);
  }

  useEffect(() => {
    if (width < 1024) {
      setShowingSearch(false);
    }
  }, [width]);

  return (
    <header ref={ref} sx={styles.wrapper}>
      <div sx={styles.right}>
        <button sx={styles.menuBtn(showingSearch)} onClick={onMenuClick}>
          <MenuIcon opened={sidebarOpened} />
        </button>
        <Logo sx={styles.logo(showingSearch)} />
        <div sx={styles.search(showingSearch)}>
          <Search
            ref={searchRef}
            indices={indices}
            showing={showingSearch}
            onClick={() => {
              handleToggleSearch();
              sidebarOpened && onMenuClick();
            }}
          />
        </div>
      </div>
      <Menu sx={styles.socialIcons(showingSearch)}>
        <ExternalLink href="https://dagster.slack.com" sx={styles.externalLink}>
          <img src={slackIcon} height={25} />
        </ExternalLink>
        <ExternalLink
          href="https://github.com/dagster-io/dagster/"
          sx={styles.externalLink}
        >
          <img src={githubIcon} height={25} />
        </ExternalLink>
        <ExternalLink
          href="https://stackoverflow.com/questions/tagged/dagster"
          sx={styles.externalLink}
        >
          <img src={stackOverflowIcon} height={25} />
        </ExternalLink>
      </Menu>
    </header>
  );
});
