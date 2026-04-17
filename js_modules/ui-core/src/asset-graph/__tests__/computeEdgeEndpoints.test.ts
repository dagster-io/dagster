import {IBounds} from '../../graph/common';
import {computeEdgeEndpoints} from '../layout';

const bounds = (x: number, y: number, width = 320, height = 100): IBounds => ({
  x,
  y,
  width,
  height,
});

describe('computeEdgeEndpoints', () => {
  describe('horizontal direction', () => {
    it('connects right edge of source to left edge of target', () => {
      const from = bounds(0, 0);
      const to = bounds(400, 0);
      const {from: ep, to: tp} = computeEdgeEndpoints(from, to, 'horizontal');

      // from: right edge of source node
      expect(ep.x).toBe(320); // x + width
      expect(ep.y).toBe(50); // y + height/2

      // to: left edge of target minus 5px
      expect(tp.x).toBe(395); // x - 5
      expect(tp.y).toBe(50); // y + height/2
    });

    it('centers vertically on the node height', () => {
      const from = bounds(0, 200, 320, 80);
      const to = bounds(500, 200, 320, 60);
      const {from: ep, to: tp} = computeEdgeEndpoints(from, to, 'horizontal');

      expect(ep.y).toBe(240); // 200 + 80/2
      expect(tp.y).toBe(230); // 200 + 60/2
    });

    it('ignores xInset in horizontal mode', () => {
      const from = bounds(0, 0);
      const to = bounds(400, 0);
      const withDefault = computeEdgeEndpoints(from, to, 'horizontal');
      const withCustomInset = computeEdgeEndpoints(from, to, 'horizontal', 16, 16);

      // xInset is irrelevant for horizontal — both should produce identical results
      expect(withDefault).toEqual(withCustomInset);
    });
  });

  describe('vertical direction', () => {
    it('connects bottom of source to top of target with default xInset', () => {
      const from = bounds(0, 0, 320, 100);
      const to = bounds(0, 200, 320, 100);
      const {from: ep, to: tp} = computeEdgeEndpoints(from, to, 'vertical');

      // from: x + xInset(24), y + height - 30
      expect(ep.x).toBe(24); // 0 + 24
      expect(ep.y).toBe(70); // 0 + 100 - 30

      // to: x + xInset(24), y + 20
      expect(tp.x).toBe(24); // 0 + 24
      expect(tp.y).toBe(220); // 200 + 20
    });

    it('respects custom fromXInset and toXInset', () => {
      const from = bounds(0, 0, 320, 100);
      const to = bounds(0, 200, 32, 50);
      const {from: ep, to: tp} = computeEdgeEndpoints(from, to, 'vertical', 16, 16);

      expect(ep.x).toBe(16); // 0 + 16
      expect(tp.x).toBe(16); // 0 + 16
    });

    it('uses xInset=24 as the default', () => {
      const from = bounds(100, 50, 320, 100);
      const to = bounds(100, 250, 320, 100);
      const {from: ep, to: tp} = computeEdgeEndpoints(from, to, 'vertical');

      expect(ep.x).toBe(124); // 100 + 24
      expect(tp.x).toBe(124); // 100 + 24
    });
  });

  describe('with node offset positions', () => {
    it('handles nodes not at origin in horizontal mode', () => {
      const from = bounds(100, 50, 320, 100);
      const to = bounds(500, 80, 320, 100);
      const {from: ep, to: tp} = computeEdgeEndpoints(from, to, 'horizontal');

      expect(ep.x).toBe(420); // 100 + 320
      expect(ep.y).toBe(100); // 50 + 100/2
      expect(tp.x).toBe(495); // 500 - 5
      expect(tp.y).toBe(130); // 80 + 100/2
    });

    it('handles nodes not at origin in vertical mode', () => {
      const from = bounds(60, 100, 320, 75);
      const to = bounds(60, 300, 320, 75);
      const {from: ep, to: tp} = computeEdgeEndpoints(from, to, 'vertical');

      expect(ep.x).toBe(84); // 60 + 24
      expect(ep.y).toBe(145); // 100 + 75 - 30
      expect(tp.x).toBe(84); // 60 + 24
      expect(tp.y).toBe(320); // 300 + 20
    });
  });
});
