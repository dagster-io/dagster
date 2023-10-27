// eslint-disable-next-line no-restricted-imports
import {GraphData} from '../../src/asset-graph/Utils';
import {LayoutAssetGraphOptions, layoutAssetGraph} from '../../src/asset-graph/layout';
import {ILayoutOp, LayoutOpGraphOptions, layoutOpGraph} from '../../src/graph/layout';

type WorkerMessageData =
  | {type: 'layoutOpGraph'; ops: ILayoutOp[]; opts: LayoutOpGraphOptions}
  | {type: 'layoutAssetGraph'; graphData: GraphData; opts: LayoutAssetGraphOptions};

// eslint-disable-next-line import/no-default-export
export default class MockWorker {
  onmessage = (_: any) => {};

  // mock expects data: { } instead of e: { data: { } }
  postMessage(data: WorkerMessageData) {
    if (data.type === 'layoutOpGraph') {
      const {ops, opts} = data;
      this.onmessage({data: layoutOpGraph(ops, opts)});
    } else if (data.type === 'layoutAssetGraph') {
      const {graphData, opts} = data;
      this.onmessage({data: layoutAssetGraph(graphData, opts)});
    }
  }
}
