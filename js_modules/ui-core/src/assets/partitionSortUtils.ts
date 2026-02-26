import {PartitionDefinitionType} from '../graphql/types';

export enum SortType {
  CREATION,
  REVERSE_CREATION,
  ALPHABETICAL,
  REVERSE_ALPHABETICAL,
}

const alphabeticalCollator = new Intl.Collator(navigator.language, {sensitivity: 'base'});

export function sortPartitionKeys(partitionKeys: string[], sortType: SortType): string[] {
  switch (sortType) {
    case SortType.CREATION:
      return partitionKeys;
    case SortType.REVERSE_CREATION:
      return [...partitionKeys].reverse();
    case SortType.ALPHABETICAL:
      return [...partitionKeys].sort(alphabeticalCollator.compare);
    case SortType.REVERSE_ALPHABETICAL:
      return [...partitionKeys].sort((a, b) => -alphabeticalCollator.compare(a, b));
  }
}

export function getDefaultPartitionSort(definitionType: PartitionDefinitionType): SortType {
  return definitionType === PartitionDefinitionType.TIME_WINDOW
    ? SortType.REVERSE_CREATION
    : SortType.CREATION;
}
