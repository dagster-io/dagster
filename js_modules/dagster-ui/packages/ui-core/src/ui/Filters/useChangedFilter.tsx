import {Box, Icon} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {useStaticSetFilter} from './useStaticSetFilter';
import {ChangeReason} from '../../graphql/types';
import {TruncatedTextWithFullTextOnHover} from '../../nav/getLeftNavItemsForOption';

export const useChangedFilter = ({
  changedInBranch,
  setChangedInBranch,
}: {
  changedInBranch?: ChangeReason[] | null;
  setChangedInBranch?: null | ((s: ChangeReason[]) => void);
}) => {
  return useStaticSetFilter<ChangeReason>({
    name: 'Changed in branch',
    icon: 'new_in_branch',
    allValues: Object.values(ChangeReason).map((reason) => ({
      key: reason,
      value: reason,
      match: [reason],
    })),
    allowMultipleSelections: true,
    menuWidth: '300px',
    renderLabel: ({value}) => (
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
    getStringValue: (value) => value[0] + value.slice(1).toLowerCase(),

    state: useMemo(() => new Set(changedInBranch ?? []), [changedInBranch]),
    onStateChanged: (values) => {
      if (setChangedInBranch) {
        setChangedInBranch(Array.from(values));
      }
    },
  });
};
