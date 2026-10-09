import {
  Box,
  Colors,
  Icon,
  Menu,
  MenuDivider,
  MenuItem,
  Popover,
  TextInput,
  Tooltip,
  UnstyledButton,
} from '@dagster-io/ui-components';
import {useContext, useMemo, useState} from 'react';

import {COMMON_COLLATOR} from '../commonCollator';
import {NavCollapseContext} from './NavCollapseProvider';
import {NavItemContent} from './NavItemContent';
import styles from './css/MainNavigation.module.css';
import {WorkspaceContext} from '../../workspace/WorkspaceContext/WorkspaceContext';

const ALL_CODE_LOCATIONS = 'All code locations';

/**
 * Scopes the whole UI to one code location. The selection is stored by the workspace context,
 * so every page that lists definitions or runs applies it and it is still set after switching
 * pages or reloading.
 */
export const CodeLocationFilterItem = () => {
  const {locationStatuses, codeLocationFilter, setCodeLocationFilter} =
    useContext(WorkspaceContext);
  const {isCollapsed} = useContext(NavCollapseContext);
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');

  const locationNames = useMemo(
    () => Object.keys(locationStatuses).sort((a, b) => COMMON_COLLATOR.compare(a, b)),
    [locationStatuses],
  );

  const matchingNames = useMemo(() => {
    const query = search.trim().toLowerCase();
    return query
      ? locationNames.filter((name) => name.toLowerCase().includes(query))
      : locationNames;
  }, [locationNames, search]);

  // With a single code location there is nothing to scope, unless a stale selection must be cleared.
  if (locationNames.length < 2 && !codeLocationFilter) {
    return null;
  }

  const select = (locationName: string | null) => {
    setCodeLocationFilter(locationName);
    setIsOpen(false);
    setSearch('');
  };

  const label = codeLocationFilter ?? ALL_CODE_LOCATIONS;

  return (
    <Popover
      isOpen={isOpen}
      onClose={() => {
        setIsOpen(false);
        setSearch('');
      }}
      placement={isCollapsed ? 'right-start' : 'bottom-start'}
      matchTargetWidth={!isCollapsed}
      content={
        <Box flex={{direction: 'column'}} style={{minWidth: 220, maxWidth: 360}}>
          {locationNames.length > 8 ? (
            <Box padding={{horizontal: 8, top: 8}}>
              <TextInput
                autoFocus
                fill
                icon="search"
                placeholder="Filter code locations…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </Box>
          ) : null}
          <Menu style={{maxHeight: 400, overflowY: 'auto'}}>
            <MenuItem
              icon="code_location"
              text={ALL_CODE_LOCATIONS}
              active={!codeLocationFilter}
              right={!codeLocationFilter ? <Icon name="done" /> : undefined}
              onClick={() => select(null)}
            />
            <MenuDivider />
            {matchingNames.map((name) => (
              <MenuItem
                key={name}
                icon="code_location"
                text={name}
                active={name === codeLocationFilter}
                right={name === codeLocationFilter ? <Icon name="done" /> : undefined}
                onClick={() => select(name)}
              />
            ))}
          </Menu>
        </Box>
      }
    >
      <Tooltip content={`Code location: ${label}`} placement="right" canShow={isCollapsed}>
        <UnstyledButton
          onClick={() => setIsOpen((current) => !current)}
          className={styles.itemButton}
          data-testid="code-location-filter"
        >
          <NavItemContent
            icon={
              <Icon
                name="code_location"
                color={codeLocationFilter ? Colors.accentBlue() : undefined}
              />
            }
            label={label}
            collapsed={isCollapsed}
            right={<Icon name="expand_more" />}
          />
        </UnstyledButton>
      </Tooltip>
    </Popover>
  );
};
