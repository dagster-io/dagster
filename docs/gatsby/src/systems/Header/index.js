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
        <Search
          ref={searchRef}
          indices={indices}
          onClick={handleToggle}
          showing={showing}
        />
      </div>
      <Menu sx={styles.socialIcons(showing)}>
        <ExternalLink href="#">
          <Slack sx={{ fill: "blue.3" }} />
        </ExternalLink>
        <ExternalLink href="#">
          <GitHub />
        </ExternalLink>
      </Menu>
    </header>
  );
});
