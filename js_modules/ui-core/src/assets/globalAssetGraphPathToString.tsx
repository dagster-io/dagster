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

export function globalAssetGraphPathForAssets(
  assetKeys: AssetKeyInput[],
  include_descendants: boolean = false,
) {
  const rawAssetsQuery = assetKeys.map((a) => `key:"${tokenForAssetKey(a)}"`).join(' or ');
  const opsQuery = `(${rawAssetsQuery})` + (include_descendants ? '+' : '');
  const opNames =
    opsQuery.length > URL_MAX_LENGTH / 2 ? [] : [assetKeys.map(tokenForAssetKey).join(',')];

  return globalAssetGraphPathToString({opNames, opsQuery});
}

export function globalAssetGraphPathForAssetsAndDescendants(assetKeys: AssetKeyInput[]) {
  return globalAssetGraphPathForAssets(assetKeys, true);
}

export function globalAssetGraphPathForGroup(groupName: string, assetKeyInContext?: AssetKeyInput) {
  return globalAssetGraphPathToString({
    opsQuery: `group:"${groupName}"`,
    opNames: assetKeyInContext ? [tokenForAssetKey(assetKeyInContext)] : [],
  });
}
