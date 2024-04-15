import {StatusCaseDot} from './util';
import {useAssetBaseData} from '../../asset-data/AssetBaseDataProvider';
import {StatusCase, buildAssetNodeStatusContent} from '../AssetNodeStatusContent';
import {GraphNode} from '../Utils';

export function StatusDot({node}: {node: Pick<GraphNode, 'assetKey' | 'definition'>}) {
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
