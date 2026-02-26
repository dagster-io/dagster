import {IconName} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {memoizedTag} from '../../asset-selection/input/util';
import {createSelectionAutoComplete} from '../../selection/SelectionAutoComplete';
import {
  SelectionAutoCompleteProvider,
  createProvider,
} from '../../selection/SelectionAutoCompleteProvider';
import {buildRepoPathForHuman} from '../../workspace/buildRepoAddress';
import {RepoAddress} from '../../workspace/types';

const iconMap: Record<(typeof automationSelectionSyntaxSupportedAttributes)[number], IconName> = {
  name: 'job',
  code_location: 'code_location',
  tag: 'tag',
  type: 'automation_condition',
  status: 'status',
};

export type Automation = {
  name: string;
  repo: RepoAddress;
  type: 'schedule' | 'sensor' | 'legacy-amp' | 'manual';
  status: 'running' | 'stopped';
  tags: {key: string; value?: string | null}[];
};

export const automationSelectionSyntaxSupportedAttributes = [
  'name',
  'code_location',
  'tag',
  'type',
  'status',
] as const;

export const useAutomationSelectionAutoCompleteProvider = <T extends Automation>(
  items: T[],
): Pick<SelectionAutoCompleteProvider, 'useAutoComplete'> => {
  const attributesMap = useMemo(() => {
    const names = new Set<string>();
    const codeLocations = new Set<string>();
    const tagSet: Set<{key: string; value: string}> = new Set();
    const types = new Set<string>();
    const statuses = new Set<string>();
    items.forEach((item) => {
      names.add(item.name);
      codeLocations.add(buildRepoPathForHuman(item.repo.name, item.repo.location));
      item.tags.forEach((tag) => {
        tagSet.add(memoizedTag(tag.key, tag.value ?? ''));
      });
      types.add(item.type);
      statuses.add(item.status);
    });
    return {
      name: Array.from(names),
      code_location: Array.from(codeLocations),
      tag: Array.from(tagSet),
      type: Array.from(types),
      status: Array.from(statuses),
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
