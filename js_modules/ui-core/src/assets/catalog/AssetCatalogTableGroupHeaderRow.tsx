import {
  Box,
  Checkbox,
  Colors,
  Icon,
  SubtitleSmall,
  UnstyledButton,
} from '@dagster-io/ui-components';
import React from 'react';

import styles from './css/StatusHeaderContainer.module.css';
import {numberFormatter} from '../../ui/formatters';

interface HeaderProps {
  icon: React.ReactNode;
  text: string;
  count: number;
  open: boolean;
  onToggleOpen: () => void;
  checkedState: 'checked' | 'indeterminate' | 'unchecked';
  onToggleChecked: (checked: boolean) => void;
}

export const AssetCatalogTableGroupHeaderRow = React.memo(
  ({icon, text, count, open, onToggleOpen, checkedState, onToggleChecked}: HeaderProps) => {
    return (
      <Box
        flex={{direction: 'row', alignItems: 'center'}}
        className={styles.container}
        border="top-and-bottom"
      >
        <div className={styles.checkboxContainer}>
          <Checkbox
            type="checkbox"
            onChange={(e) => onToggleChecked(e.target.checked)}
            size="small"
            checked={checkedState !== 'unchecked'}
            indeterminate={checkedState === 'indeterminate'}
          />
        </div>
        <UnstyledButton onClick={onToggleOpen} style={{flex: 1}}>
          <Box
            flex={{direction: 'row', alignItems: 'center', gap: 4, justifyContent: 'space-between'}}
          >
            <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
              {icon}
              <SubtitleSmall>
                {text} ({numberFormatter.format(count)})
              </SubtitleSmall>
            </Box>
            <Box padding={{right: 8}}>
              <Icon
                name="arrow_drop_down"
                style={{transform: open ? 'rotate(0deg)' : 'rotate(-90deg)'}}
                color={Colors.textLight()}
              />
            </Box>
          </Box>
        </UnstyledButton>
      </Box>
    );
  },
);

AssetCatalogTableGroupHeaderRow.displayName = 'AssetCatalogTableGroupHeaderRow';
