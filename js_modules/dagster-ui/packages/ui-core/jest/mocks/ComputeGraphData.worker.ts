import {setFeatureFlagsInternal} from '../../src/app/Flags';
import {computeGraphData} from '../../src/asset-graph/ComputeGraphData';
import {ComputeGraphDataMessageType} from '../../src/asset-graph/ComputeGraphData.types';

// eslint-disable-next-line import/no-default-export
export default class MockWorker {
  onmessage = (_: any) => {};

  addEventListener(_type: string, handler: any) {
    this.onmessage = handler;
  }

  // mock expects data: { } instead of e: { data: { } }
  async postMessage(data: ComputeGraphDataMessageType) {
    if (data.type === 'computeGraphData') {
      if (data.flagAssetSelectionSyntax) {
        setFeatureFlagsInternal({flagAssetSelectionSyntax: true});
      }
      const state = await computeGraphData(data);
      this.onmessage({data: state});
    }
  }
}

const originalWorker = global.Worker;
// @ts-expect-error - test shenanigans
global.Worker = function ComputeGraphDataMockWorkerWrapper(
  url: string | URL,
  opts?: WorkerOptions,
) {
  if (url.toString().endsWith('ComputeGraphData.worker')) {
    return new MockWorker();
  } else {
    return new originalWorker(url, opts);
  }
};
