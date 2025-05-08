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
  const opsQuery = assetKeys.map((a) => `key:"${tokenForAssetKey(a)}"+`).join(' or ');
  const opNames =
    opsQuery.length > URL_MAX_LENGTH / 2 ? [] : [assetKeys.map(tokenForAssetKey).join(',')];

  return globalAssetGraphPathToString({opNames, opsQuery});
}
