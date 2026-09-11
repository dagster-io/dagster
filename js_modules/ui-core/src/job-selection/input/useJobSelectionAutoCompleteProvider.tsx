import {IconName} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {DEFAULT_JOB_GROUP_NAME} from '../../jobs/jobGroups';
import {createSelectionAutoComplete} from '../../selection/SelectionAutoComplete';
import {
  SelectionAutoCompleteProvider,
  createProvider,
} from '../../selection/SelectionAutoCompleteProvider';
import {buildRepoPathForHuman} from '../../workspace/buildRepoAddress';
import {Job} from '../AntlrJobSelection';

const iconMap: Record<(typeof jobSelectionSyntaxSupportedAttributes)[number], IconName> = {
  name: 'job',
  group: 'asset_group',
  code_location: 'code_location',
};

export const jobSelectionSyntaxSupportedAttributes = ['name', 'group', 'code_location'] as const;

export const useJobSelectionAutoCompleteProvider = <T extends Job>(
  items: T[],
): Pick<SelectionAutoCompleteProvider, 'useAutoComplete'> => {
  const attributesMap = useMemo(() => {
    const names = new Set<string>();
    const groups = new Set<string>();
    const codeLocations = new Set<string>();
    items.forEach((item) => {
      names.add(item.name);
      groups.add(item.groupName || DEFAULT_JOB_GROUP_NAME);
      codeLocations.add(buildRepoPathForHuman(item.repo.name, item.repo.location));
    });
    return {
      name: Array.from(names),
      group: Array.from(groups),
      code_location: Array.from(codeLocations),
    };
  }, [items]);

  const baseProvider = useMemo(
    () => ({
      ...createProvider({
        attributesMap,
        primaryAttributeKey: 'name',
        attributeToIcon: iconMap,
        functions: [],
      }),
      supportsTraversal: false,
    }),
    [attributesMap],
  );
  const selectionHint = useMemo(() => createSelectionAutoComplete(baseProvider), [baseProvider]);

  return useMemo(
    () => ({
      useAutoComplete: ({line, cursorIndex}) => {
        const autoCompleteResults = useMemo(
          () => selectionHint(line, cursorIndex),
          [line, cursorIndex],
        );
        return {
          autoCompleteResults,
          loading: false,
        };
      },
    }),
    [selectionHint],
  );
};
