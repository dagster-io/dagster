import { layoutPipeline, IPipelineLayoutParams } from "../../src/graph/layout";

export default class MockWorker {
  onmessage = (_: any) => {};

  // mock expects data: { } instead of e: { data: { } }
  postMessage(data: IPipelineLayoutParams) {
    this.onmessage({ data: layoutPipeline(data) });
  }
}
