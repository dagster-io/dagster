import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

import {computeGraphData} from './ComputeGraphData';
import {ComputeGraphDataMessageType} from './ComputeGraphData.types';
import {setFeatureFlags} from '../app/Flags';

type WorkerMessageData = ComputeGraphDataMessageType;

self.addEventListener('message', async (event: MessageEvent & {data: WorkerMessageData}) => {
  const {data} = event;

  if (data.type === 'computeGraphData') {
    if (data.flagAssetSelectionSyntax) {
      setFeatureFlags({[FeatureFlag.flagAssetSelectionSyntax]: true});
    }
    const state = await computeGraphData(data);
    self.postMessage(state);
  }
});

self.onmessage = function (event) {
  if (event.data === 'close') {
    self.close(); // Terminates the worker
  }
};
