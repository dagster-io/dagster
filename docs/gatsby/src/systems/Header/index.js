/** @jsx jsx */
import { jsx } from "theme-ui";
import { forwardRef, useEffect, useRef } from "react";
import { Slack, GitHub } from "react-feather";
import { useMachine } from "@xstate/react";
import useClickAway from "react-use/lib/useClickAway";
import useKeyPressEvent from "react-use/lib/useKeyPressEvent";
import useWindowSize from "react-use/lib/useWindowSize";

import { ExternalLink, Menu, Logo } from "systems/Core";
import { Search } from "systems/Search";

import githubIcon from "./images/github-icon.svg";
import slackIcon from "./images/slack-icon.svg";
import stackOverflowIcon from "./images/stack-overflow-icon.svg";

import { MenuIcon } from "./components/MenuIcon";
import { headerMachine } from "./machines/header";
import * as styles from "./styles";

const indices = [
  { name: `Pages`, title: `Pages`, hitComp: `PageHit` },
  { name: `Modules`, title: `Modules`, hitComp: `ModuleHit` }
];

export const Header = forwardRef(({ onMenuClick, sidebarOpened }, ref) => {
  const searchRef = useRef(null);
  const { width } = useWindowSize();
  const [state, send] = useMachine(headerMachine.withContext({ width }));

  const showing = state.matches("opened");

  function handleToggle() {
    send("TOGGLE");
  }

  useEffect(() => {
    send("SET_INITIAL_WIDTH", { data: width });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    send("SET_WIDTH", { data: width });
  }, [width, send]);

  useKeyPressEvent("Escape", () => {
    if (showing) handleToggle();
  });

  useClickAway(searchRef, () => {
    if (showing) handleToggle();
  });

  return (
    <header ref={ref} sx={styles.wrapper}>
      <div sx={styles.right}>
        <button sx={styles.menuBtn(showing)} onClick={onMenuClick}>
          <MenuIcon opened={sidebarOpened} />
        </button>
        <Logo sx={styles.logo(showing)} />
        <div sx={styles.search(showing)}>
          <Search
            ref={searchRef}
            indices={indices}
            onClick={handleToggle}
            showing={showing}
          />
        </div>
      </div>
      <Menu sx={styles.socialIcons(showing)}>
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
