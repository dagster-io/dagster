// eslint-disable-next-line no-restricted-imports
import {layoutPipeline, IPipelineLayoutParams} from '../../src/graph/layout';

// eslint-disable-next-line import/no-default-export
export default class MockWorker {
  onmessage = (_: any) => {};

  // mock expects data: { } instead of e: { data: { } }
  postMessage(data: IPipelineLayoutParams) {
    this.onmessage({data: layoutPipeline(data.solids)});
  }
}
