import {StatusCaseDot} from './util';
import {useAssetLiveData} from '../../asset-data/AssetLiveDataProvider';
import {
  StatusCase,
  StatusContentArgs,
  buildAssetNodeStatusContent,
} from '../AssetNodeStatusContent';
import {AssetKeyInput} from '../../graphql/types';

export type StatusDotNode = {assetKey: AssetKeyInput; definition: StatusContentArgs['definition']};

export function StatusDot({node}: {node: StatusDotNode}) {
  const {liveData} = useAssetLiveData(node.assetKey);

  if (!liveData) {
    return <StatusCaseDot statusCase={StatusCase.LOADING} />;
  }
  const status = buildAssetNodeStatusContent({
    assetKey: node.assetKey,
    definition: node.definition,
    liveData,
    expanded: true,
  });
  return <StatusCaseDot statusCase={status.case} />;
}
