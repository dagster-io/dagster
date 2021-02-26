import {Colors, Icon} from '@blueprintjs/core';
import * as React from 'react';
import {Link, LinkProps, useHistory, useLocation} from 'react-router-dom';
import styled from 'styled-components';

import {ShortcutHandler} from 'src/app/ShortcutHandler';
import navBarImage from 'src/images/nav-logo-icon.png';
import navTitleImage from 'src/images/nav-title.png';
import {VersionNumber} from 'src/nav/VersionNumber';
import {config, matchSome, NavItemConfig} from 'src/nav/config';
import {shortcutLabel} from 'src/nav/shortcutLabel';
import {SearchDialog} from 'src/search/SearchDialog';
import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';

interface NavItemProps extends NavItemConfig {
  pathname: string;
}

const NavItem: React.FC<NavItemProps> = React.memo(
  ({label, to, icon, matchingPaths, pathname, shortcut}) => {
    const history = useHistory();

    const item = (
      <Item to={to} key={to} $active={matchSome(pathname, matchingPaths)}>
        <Icon icon={icon} iconSize={12} className="navIcon" />
        {label}
      </Item>
    );

    const filter = React.useCallback(
      (e: KeyboardEvent) => {
        if (e.code === shortcut?.code) {
          const modCount =
            Number(e.getModifierState('Alt')) +
            Number(e.getModifierState('Ctrl')) +
            Number(e.getModifierState('Shift')) +
            Number(e.getModifierState('Meta'));

          return !!(
            (!shortcut.modifier && modCount === 0) ||
            (modCount === 1 && shortcut.modifier && e.getModifierState(shortcut.modifier))
          );
        }
        return false;
      },
      [shortcut],
    );

    if (shortcut) {
      return (
        <ShortcutHandler
          onShortcut={() => history.push(to)}
          shortcutLabel={shortcutLabel(shortcut)}
          shortcutFilter={filter}
        >
          {item}
        </ShortcutHandler>
      );
    }
    return item;
  },
);

export const LeftNavSimple = React.memo(() => {
  const {pathname} = useLocation();

  const items = config.map((section, ii) => (
    <div key={`section-${ii}`}>
      {section.map((config) => (
        <NavItem key={config.to} pathname={pathname} {...config} />
      ))}
    </div>
  ));

  return (
    <Box
      flex={{direction: 'column', justifyContent: 'space-between', shrink: 0}}
      style={{width: '188px'}}
      border={{side: 'right', width: 1, color: Colors.LIGHT_GRAY3}}
    >
      <Group direction="column" spacing={16}>
        <Group direction="column" spacing={12} padding={{top: 20, horizontal: 12}}>
          <Group direction="row" alignItems="center" spacing={8} padding={{horizontal: 4}}>
            <img alt="logo" src={navBarImage} style={{display: 'block', height: 28}} />
            <Group direction="column" spacing={2} padding={{top: 2}}>
              <img
                src={navTitleImage}
                style={{display: 'block', height: 10, filter: 'brightness(0.05)'}}
                alt="title"
              />
              <VersionNumber />
            </Group>
          </Group>
          <Box padding={{right: 4}}>
            <SearchDialog />
          </Box>
        </Group>
        {items}
      </Group>
    </Box>
  );
});

interface ItemProps extends LinkProps {
  $active?: boolean;
}

const Item = styled(Link)<ItemProps>`
  align-items: center;
  background-color: ${({$active}) => ($active ? Colors.LIGHT_GRAY4 : 'transparent')};
  color: ${({$active}) => ($active ? Colors.BLUE2 : Colors.DARK_GRAY2)};
  cursor: pointer;
  display: flex;
  flex-direction: row;
  font-weight: ${({$active}) => ($active ? 600 : 400)};
  padding: 4px 0 4px 22px;
  user-select: none;
  transition: background 0.1s linear;

  .navIcon.bp3-icon {
    display: block;
    margin-right: 8px;
  }

  .navIcon.bp3-icon svg {
    fill: ${({$active}) => ($active ? Colors.BLUE2 : Colors.DARK_GRAY3)};
  }

  &:hover {
    color: ${Colors.BLUE2};
    text-decoration: none;
  }

  &:hover .navIcon.bp3-icon svg {
    fill: ${Colors.BLUE2};
  }
`;
