import {createWorkerThread} from 'shared/workers/WorkerThread.oss';

import {computeGraphData} from './ComputeGraphData';
import {BuildGraphDataMessageType, ComputeGraphDataMessageType} from './ComputeGraphData.types';
import {buildGraphData} from './Utils';

type WorkerMessageData = ComputeGraphDataMessageType | BuildGraphDataMessageType;

createWorkerThread(
  async (postMessage: (message: any) => void, data: WorkerMessageData) => {
    console.log({data});
    if (data.type === 'computeGraphData') {
      const state = await computeGraphData(data);
      postMessage({...state, id: data.id});
    } else if (data.type === 'buildGraphData') {
      postMessage({...buildGraphData(data.nodes), id: data.id});
    }
  },
  (_postMessage: (message: any) => void, error: Error) => {
    console.error(error);
  },
);
