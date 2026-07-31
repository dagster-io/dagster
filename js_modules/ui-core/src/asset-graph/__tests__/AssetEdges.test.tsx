import {MAX_EDGES, getEdgesToShow} from '../AssetEdges';
import {AssetLayoutEdge} from '../layout';

const viewportRect = {top: 0, left: 0, right: 1000, bottom: 1000};

const buildEdges = (): AssetLayoutEdge[] =>
  Array.from({length: 250}, (_, index) => ({
    from: {x: index, y: index},
    fromId: `from-${index}`,
    to: {x: index + 1, y: index + 1},
    toId: `to-${index}`,
    sourceBoundary: 400,
    targetBoundary: 600,
  }));

describe('getEdgesToShow', () => {
  it('caps visible edges and retains routed geometry metadata', () => {
    const {edgesToShow} = getEdgesToShow(
      {
        edges: buildEdges(),
        highlighted: null,
        selected: null,
        viewportRect,
      },
      MAX_EDGES,
    );

    expect(MAX_EDGES).toBe(200);
    expect(edgesToShow).toHaveLength(200);
    expect(edgesToShow[0]).toEqual(
      expect.objectContaining({sourceBoundary: 400, targetBoundary: 600}),
    );
  });

  it('caps selected or highlighted edges', () => {
    const edges = buildEdges();
    const {selectedOrHighlightedEdges} = getEdgesToShow(
      {
        edges,
        highlighted: edges.map(({fromId}) => fromId),
        selected: null,
        viewportRect,
      },
      MAX_EDGES,
    );

    expect(selectedOrHighlightedEdges).toHaveLength(MAX_EDGES);
  });

  // getEdgesToShow runs inside a web worker via @koale/useworker, which serializes it with
  // fn.toString() and runs it with no module closure. Any module-scope identifier it references
  // becomes a ReferenceError in the worker, is swallowed by its try/catch, and every edge
  // disappears. Reconstructing the function in global-only scope reproduces the worker exactly.
  it('does not depend on module scope when serialized into a worker', () => {
    const edges = buildEdges();
    const serialized = getEdgesToShow.toString();
    // eslint-disable-next-line @typescript-eslint/no-implied-eval
    const reconstructed = new Function(`return (${serialized})`)() as typeof getEdgesToShow;

    const {edgesToShow} = reconstructed(
      {edges, highlighted: null, selected: null, viewportRect},
      MAX_EDGES,
    );

    expect(edgesToShow).toHaveLength(MAX_EDGES);
  });
});
