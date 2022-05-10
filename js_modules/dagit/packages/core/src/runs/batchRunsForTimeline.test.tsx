import {batchRunsForTimeline, RunWithTime} from './batchRunsForTimeline';

describe('batchRunsForTimeline', () => {
  const start = 0;
  const end = 100;
  const width = 100;
  const minChunkWidth = 2;
  const minMultipleWidth = 18;

  const getBatch = (runs: RunWithTime[]) =>
    batchRunsForTimeline({runs, start, end, width, minChunkWidth, minMultipleWidth});

  describe('Overlapping', () => {
    /**
     * [      ]
     *      [      ]
     */
    it('batches partially overlapping runs', () => {
      const runA = {startTime: 10, endTime: 50};
      const runB = {startTime: 30, endTime: 70};
      const runs = [runA, runB];

      const batched = getBatch(runs);
      expect(batched.length).toBe(1);
      const batch = batched[0];
      expect(batch.startTime).toBe(10);
      expect(batch.endTime).toBe(70);
      expect(batch.left).toBe(10);
      expect(batch.width).toBe(60);
      expect(batch.runs).toContain(runA);
      expect(batch.runs).toContain(runB);
    });

    /**
     * [               ]
     *      [      ]
     */
    it('batches runs where one is completely overlapped by the other', () => {
      const runA = {startTime: 10, endTime: 50};
      const runB = {startTime: 30, endTime: 40};
      const runs = [runA, runB];

      const batched = getBatch(runs);
      expect(batched.length).toBe(1);
      const batch = batched[0];
      expect(batch.startTime).toBe(10);
      expect(batch.endTime).toBe(50);
      expect(batch.left).toBe(10);
      expect(batch.width).toBe(40);
      expect(batch.runs).toContain(runA);
      expect(batch.runs).toContain(runB);
    });

    /**
     * [      ]
     *     [      ]
     *          [      ]
     */
    it('batches 3+ overlapping items', () => {
      const runA = {startTime: 10, endTime: 50};
      const runB = {startTime: 30, endTime: 60};
      const runC = {startTime: 40, endTime: 90};
      const runs = [runA, runB, runC];

      const batched = getBatch(runs);
      expect(batched.length).toBe(1);
      const batch = batched[0];
      expect(batch.startTime).toBe(10);
      expect(batch.endTime).toBe(90);
      expect(batch.left).toBe(10);
      expect(batch.width).toBe(80);
      expect(batch.runs).toContain(runA);
      expect(batch.runs).toContain(runB);
      expect(batch.runs).toContain(runC);
    });

    /**
     * [      ]
     *          [      ]
     *     [      ]
     */
    it('batches 3+ overlapping items even when consecutive items in `runs` are not overlapping', () => {
      const runA = {startTime: 10, endTime: 50};
      const runB = {startTime: 60, endTime: 90};
      const runC = {startTime: 40, endTime: 70};
      const runs = [runA, runB, runC];

      const batched = getBatch(runs);
      expect(batched.length).toBe(1);
      const batch = batched[0];
      expect(batch.startTime).toBe(10);
      expect(batch.endTime).toBe(90);
      expect(batch.left).toBe(10);
      expect(batch.width).toBe(80);
      expect(batch.runs).toContain(runA);
      expect(batch.runs).toContain(runB);
      expect(batch.runs).toContain(runC);
    });

    /**
     * [      ]
     *       [            ]
     */
    it('batches items when one is at the very end, i.e. still running', () => {
      const runA = {startTime: 10, endTime: 50};
      const runB = {startTime: 40, endTime: 100};
      const runs = [runA, runB];

      const batched = getBatch(runs);
      expect(batched.length).toBe(1);
      const batch = batched[0];
      expect(batch.startTime).toBe(10);
      expect(batch.endTime).toBe(100);
      expect(batch.left).toBe(10);
      expect(batch.width).toBe(90);
      expect(batch.runs).toContain(runA);
      expect(batch.runs).toContain(runB);
    });

    /**
     * [      ]
     *        [      ]
     */
    it('treats equal endpoints as overlapping', () => {
      const runA = {startTime: 10, endTime: 50};
      const runB = {startTime: 50, endTime: 70};
      const runs = [runA, runB];

      const batched = getBatch(runs);
      expect(batched.length).toBe(1);
      const batch = batched[0];
      expect(batch.startTime).toBe(10);
      expect(batch.endTime).toBe(70);
      expect(batch.left).toBe(10);
      expect(batch.width).toBe(60);
      expect(batch.runs).toContain(runA);
      expect(batch.runs).toContain(runB);
    });
  });

  describe('Non-overlapping', () => {
    /**
     * [      ]
     *           [      ]
     */
    it('does not batch non-overlapping runs', () => {
      const runA = {startTime: 10, endTime: 30};
      const runB = {startTime: 40, endTime: 70};
      const runs = [runA, runB];

      const batched = getBatch(runs);
      expect(batched.length).toBe(2);

      // Batch A contains the later run due to sorting.
      const [batchB, batchA] = batched;

      expect(batchA.startTime).toBe(10);
      expect(batchA.endTime).toBe(30);
      expect(batchA.left).toBe(10);
      expect(batchA.width).toBe(20);
      expect(batchA.runs).toContain(runA);

      expect(batchB.startTime).toBe(40);
      expect(batchB.endTime).toBe(70);
      expect(batchB.left).toBe(40);
      expect(batchB.width).toBe(30);
      expect(batchB.runs).toContain(runB);
    });

    /**
     * [      ]
     *           [      ]
     *                    [      ]
     */
    it('does not batch 3+ non-overlapping runs', () => {
      const runA = {startTime: 10, endTime: 30};
      const runB = {startTime: 40, endTime: 70};
      const runC = {startTime: 80, endTime: 90};
      const runs = [runA, runB, runC];

      const batched = getBatch(runs);
      expect(batched.length).toBe(3);

      // Sorting results in later runs being in the first batch.
      const [batchC, batchB, batchA] = batched;

      expect(batchA.startTime).toBe(10);
      expect(batchA.endTime).toBe(30);
      expect(batchA.left).toBe(10);
      expect(batchA.width).toBe(20);
      expect(batchA.runs).toContain(runA);

      expect(batchB.startTime).toBe(40);
      expect(batchB.endTime).toBe(70);
      expect(batchB.left).toBe(40);
      expect(batchB.width).toBe(30);
      expect(batchB.runs).toContain(runB);

      expect(batchC.startTime).toBe(80);
      expect(batchC.endTime).toBe(90);
      expect(batchC.left).toBe(80);
      expect(batchC.width).toBe(10);
      expect(batchC.runs).toContain(runC);
    });
  });

  describe('Minimum widths', () => {
    it('uses minimum chunk width for tiny runs', () => {
      const tinyRun = {startTime: 10, endTime: 11};
      const batched = getBatch([tinyRun]);

      const [batch] = batched;
      expect(batch.startTime).toBe(10);
      expect(batch.endTime).toBe(11);
      expect(batch.left).toBe(10);
      expect(batch.width).toBe(minChunkWidth);
      expect(batch.runs).toContain(tinyRun);
    });

    it('uses minimum multiple-run width for batched runs', () => {
      const tinyRunA = {startTime: 10, endTime: 11};
      const tinyRunB = {startTime: 10, endTime: 12};
      const batched = getBatch([tinyRunA, tinyRunB]);

      const [batch] = batched;
      expect(batch.startTime).toBe(10);
      expect(batch.endTime).toBe(12);
      expect(batch.left).toBe(10);
      expect(batch.width).toBe(minMultipleWidth);
      expect(batch.runs).toContain(tinyRunA);
      expect(batch.runs).toContain(tinyRunB);
    });
  });
});
