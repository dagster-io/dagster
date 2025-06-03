import {Icon, Tooltip} from '@dagster-io/ui-components';
import {useCallback} from 'react';

import {useSearchDialog} from './SearchDialog';
import {ShortcutHandler} from '../app/ShortcutHandler';
import {TooltipShortcutInfo, TopNavButton} from '../app/TopNavButton';

export const SearchTopNavItem = () => {
  const {openSearch, overlay} = useSearchDialog();

  const shortcutFilter = useCallback((e: KeyboardEvent) => {
    if (e.altKey || e.shiftKey) {
      return false;
    }

    if (e.ctrlKey || e.metaKey) {
      return e.code === 'KeyK';
    }

    return e.code === 'Slash';
  }, []);

  return (
    <>
      <ShortcutHandler onShortcut={openSearch} shortcutLabel="/" shortcutFilter={shortcutFilter}>
        <Tooltip
          content={<TooltipShortcutInfo label="Search" shortcutKey="/" />}
          placement="bottom"
        >
          <TopNavButton onClick={openSearch}>
            <Icon name="search" size={20} />
          </TopNavButton>
        </Tooltip>
      </ShortcutHandler>
      {overlay}
    </>
  );
};
