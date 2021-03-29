import {layoutPipeline} from '../graph/layout';
// eslint-disable-next-line no-restricted-globals
const ctx: Worker = self as any;

ctx.addEventListener('message', async (event) => {
  const {solids, parentSolid} = event.data;
  const layout = layoutPipeline(solids, parentSolid);
  ctx.postMessage(layout);
});
