import {Box, Button, Colors, Icon, Tooltip} from '@dagster-io/ui-components';

import {KeyboardTag} from './KeyboardTag';
import {AssetLayoutDirection} from './layout';
import {ShortcutHandler} from '../app/ShortcutHandler';
import {useStateWithStorage} from '../hooks/useStateWithStorage';

export const ToggleGroupsButton = ({
  expandedGroups,
  setExpandedGroups,
  allGroups,
}: {
  expandedGroups: string[];
  setExpandedGroups: (v: string[]) => void;
  allGroups: string[];
}) => (
  <ShortcutHandler
    shortcutLabel="⌥E"
    onShortcut={() => setExpandedGroups(expandedGroups.length === 0 ? allGroups : [])}
    shortcutFilter={(e) => e.altKey && e.code === 'KeyE'}
  >
    {expandedGroups.length === 0 ? (
      <Tooltip
        content={
          <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
            Expand all groups <KeyboardTag $withinTooltip>⌥E</KeyboardTag>
          </Box>
        }
      >
        <Button
          icon={<Icon name="unfold_more" />}
          onClick={() => setExpandedGroups(allGroups)}
          style={{background: Colors.backgroundDefault()}}
        />
      </Tooltip>
    ) : (
      <Tooltip
        content={
          <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
            Collapse all groups <KeyboardTag $withinTooltip>⌥E</KeyboardTag>
          </Box>
        }
      >
        <Button
          icon={<Icon name="unfold_less" />}
          onClick={() => setExpandedGroups([])}
          style={{background: Colors.backgroundDefault()}}
        />
      </Tooltip>
    )}
  </ShortcutHandler>
);

export const useLayoutDirectionState = () =>
  useStateWithStorage<AssetLayoutDirection>('asset-graph-direction', (json) =>
    ['vertical', 'horizontal'].includes(json) ? json : 'horizontal',
  );

export const ToggleDirectionButton = ({
  direction,
  setDirection,
}: {
  direction: AssetLayoutDirection;
  setDirection: (d: AssetLayoutDirection) => void;
}) => (
  <ShortcutHandler
    shortcutLabel="⌥O"
    onShortcut={() => setDirection(direction === 'vertical' ? 'horizontal' : 'vertical')}
    shortcutFilter={(e) => e.altKey && e.code === 'KeyO'}
  >
    {direction === 'horizontal' ? (
      <Tooltip
        content={
          <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
            Change graph to vertical orientation <KeyboardTag $withinTooltip>⌥O</KeyboardTag>
          </Box>
        }
      >
        <Button
          icon={<Icon name="graph_horizontal" />}
          onClick={() => setDirection('vertical')}
          style={{background: Colors.backgroundDefault()}}
        />
      </Tooltip>
    ) : (
      <Tooltip
        content={
          <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
            Change graph to horizontal orientation <KeyboardTag $withinTooltip>⌥O</KeyboardTag>
          </Box>
        }
      >
        <Button
          icon={<Icon name="graph_vertical" />}
          onClick={() => setDirection('horizontal')}
          style={{background: Colors.backgroundDefault()}}
        />
      </Tooltip>
    )}
  </ShortcutHandler>
);
