import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

import {computeGraphData} from './ComputeGraphData';
import {BuildGraphDataMessageType, ComputeGraphDataMessageType} from './ComputeGraphData.types';
import {buildGraphData} from './Utils';
import {setFeatureFlags} from '../app/Flags';
import {assertUnreachable} from '../app/Util';

type WorkerMessageData = ComputeGraphDataMessageType | BuildGraphDataMessageType;

self.addEventListener('message', async (event: MessageEvent & {data: WorkerMessageData}) => {
  const data: WorkerMessageData = event.data;

  if (data.flagSelectionSyntax) {
    setFeatureFlags({[FeatureFlag.flagSelectionSyntax]: true});
  }

  if (data.type === 'computeGraphData') {
    const state = await computeGraphData(data);
    self.postMessage({...state, id: data.id});
  } else if (data.type === 'buildGraphData') {
    self.postMessage({...buildGraphData(data.nodes), id: data.id});
  } else {
    assertUnreachable(data);
  }
});

self.onmessage = function (event) {
  if (event.data === 'close') {
    self.close(); // Terminates the worker
  }
};
