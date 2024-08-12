import {Box, Icon} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {ChangeReason} from '../../graphql/types';
import {TruncatedTextWithFullTextOnHover} from '../../nav/getLeftNavItemsForOption';
import {StaticBaseConfig, useStaticSetFilter} from '../BaseFilters/useStaticSetFilter';

export const ALL_VALUES = Object.values(ChangeReason).map((reason) => ({
  key: reason,
  value: reason,
  match: [reason],
}));

export const useChangedFilter = ({
  changedInBranch,
  setChangedInBranch,
}: {
  changedInBranch?: ChangeReason[] | null;
  setChangedInBranch?: null | ((s: ChangeReason[]) => void);
}) => {
  return useStaticSetFilter<ChangeReason>({
    allValues: ALL_VALUES,
    allowMultipleSelections: true,
    menuWidth: '300px',
    ...BaseConfig,

    state: useMemo(() => new Set(changedInBranch ?? []), [changedInBranch]),
    onStateChanged: (values) => {
      if (setChangedInBranch) {
        setChangedInBranch(Array.from(values));
      }
    },
  });
};

export const BaseConfig: StaticBaseConfig<ChangeReason> = {
  name: 'Changed in branch',
  icon: 'new_in_branch',
  renderLabel: ({value}: {value: ChangeReason}) => (
    <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
      <Icon name="new_in_branch" />
      <TruncatedTextWithFullTextOnHover
        tooltipText={value}
        text={
          <span style={{textTransform: 'capitalize'}}>
            {value.toLocaleLowerCase().replace('_', ' ')}
          </span>
        }
      />
    </Box>
  ),
  getStringValue: (value: ChangeReason) => value[0] + value.slice(1).toLowerCase(),
};
