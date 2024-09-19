import {tokenForAssetKey} from '../asset-graph/Utils';
import {AssetKeyInput} from '../graphql/types';
import {
  ExplorerPath,
  explorerPathFromString,
  explorerPathToString,
} from '../pipelines/PipelinePathUtils';

// https://stackoverflow.com/questions/417142/what-is-the-maximum-length-of-a-url-in-different-browsers
const URL_MAX_LENGTH = 32000;
const __GLOBAL__ = '__GLOBAL__';

export function globalAssetGraphPathToString(path: Omit<ExplorerPath, 'pipelineName'>) {
  const str = explorerPathToString({...path, pipelineName: __GLOBAL__}).replace(__GLOBAL__, '');
  return `/asset-groups${str}`;
}

export function globalAssetGraphPathFromString(pathName: string) {
  return explorerPathFromString(__GLOBAL__ + pathName || '/');
}

export function globalAssetGraphPathForAssetsAndDescendants(assetKeys: AssetKeyInput[]) {
  // In a perfect world we populate ops query to "asset1*,asset2*" and then select the roots
  // by passing opNames. If we don't have enough characters to do both, just populate the ops
  // query. It might still be too long, but we tried.
  const opsQuery = assetKeys.map((a) => `${tokenForAssetKey(a)}*`).join(', ');
  const opNames =
    opsQuery.length > URL_MAX_LENGTH / 2 ? [] : [assetKeys.map(tokenForAssetKey).join(',')];
  return globalAssetGraphPathToString({opNames, opsQuery});
}
