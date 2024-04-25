import {StatusCaseDot} from './util';
import {useAssetBaseData} from '../../asset-data/AssetBaseDataProvider';
import {AssetKeyInput} from '../../graphql/types';
import {
  StatusCase,
  StatusContentArgs,
  buildAssetNodeStatusContent,
} from '../AssetNodeStatusContent';

export type StatusDotNode = {assetKey: AssetKeyInput; definition: StatusContentArgs['definition']};

export function StatusDot({node}: {node: StatusDotNode}) {
  const {liveData} = useAssetBaseData(node.assetKey);

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
