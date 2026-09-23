import {MappedRunsFeedEntry} from './mapRunsFeedData';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {RepoAddress} from '../../workspace/types';

export const buildTagMap = (tags: {key: string; value: string}[]) =>
  new Map(tags.map(({key, value}) => [key, value]));

export const getRepoAddress = (entry: MappedRunsFeedEntry): RepoAddress | null =>
  entry.__typename === 'Run' && entry.repositoryOrigin !== null
    ? buildRepoAddress(
        entry.repositoryOrigin.repositoryName,
        entry.repositoryOrigin.repositoryLocationName,
      )
    : null;
