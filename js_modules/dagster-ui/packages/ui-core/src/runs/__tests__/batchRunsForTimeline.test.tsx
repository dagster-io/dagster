import {RunWithTime, batchRunsForTimeline} from '../batchRunsForTimeline';

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
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      const batch = batched[0]!;
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
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      const batch = batched[0]!;
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
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      const batch = batched[0]!;
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
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      const batch = batched[0]!;
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
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      const batch = batched[0]!;
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
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      const batch = batched[0]!;
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

      // Batch A contains the earlier run due to sorting.
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      const batchA = batched[0]!;
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      const batchB = batched[1]!;

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

      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      const batchA = batched[0]!;
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      const batchB = batched[1]!;
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      const batchC = batched[2]!;

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

      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      const batch = batched[0]!;
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

      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      const batch = batched[0]!;
      expect(batch.startTime).toBe(10);
      expect(batch.endTime).toBe(12);
      expect(batch.left).toBe(10);
      expect(batch.width).toBe(minMultipleWidth);
      expect(batch.runs).toContain(tinyRunA);
      expect(batch.runs).toContain(tinyRunB);
    });
  });

  describe('Overlap with "now"', () => {
    let realDate: any;
    beforeEach(() => {
      realDate = Date.now();
    });

    afterAll(() => {
      Date.now = realDate;
    });

    /**
     *                   | <- NOW
     * [      ]
     *         [      ]
     */
    it('does batch adjacent runs if they do not overlap with "now"', () => {
      Date.now = jest.fn(() => 80);
      const runA = {startTime: 10, endTime: 40};
      const runB = {startTime: 40, endTime: 70};
      const runs = [runA, runB];

      const batched = getBatch(runs);
      expect(batched.length).toBe(1);
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      const batch = batched[0]!;
      expect(batch.startTime).toBe(10);
      expect(batch.endTime).toBe(70);
      expect(batch.left).toBe(10);
      expect(batch.width).toBe(60);
      expect(batch.runs).toContain(runA);
      expect(batch.runs).toContain(runB);
    });

    /**
     *         | <- NOW
     * [      ]
     *         [      ]
     */
    it('does not batch adjacent runs if they also would overlap with "now"', () => {
      Date.now = jest.fn(() => 40);
      const runA = {startTime: 10, endTime: 40};
      const runB = {startTime: 40, endTime: 70};
      const runs = [runA, runB];

      const batched = getBatch(runs);
      expect(batched.length).toBe(2);

      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      const batchA = batched[0]!;
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      const batchB = batched[1]!;

      expect(batchA.startTime).toBe(10);
      expect(batchA.endTime).toBe(40);
      expect(batchA.left).toBe(10);
      expect(batchA.width).toBe(30);
      expect(batchA.runs).toContain(runA);

      expect(batchB.startTime).toBe(40);
      expect(batchB.endTime).toBe(70);
      expect(batchB.left).toBe(40);
      expect(batchB.width).toBe(30);
      expect(batchB.runs).toContain(runB);
    });
  });

  describe('Pre-batch sort order', () => {
    // This is a case where sort by descending `start` value results in
    // incorrect batching, but sort by ascending `start` value results in correct
    // batching.
    it('batches correctly for the strange sorting case', () => {
      Date.now = jest.fn(() => 82600000);

      const runs = [
        // Here's a batch:
        {startTime: 82167812, endTime: 82247921},
        {startTime: 82194099, endTime: 82264135},
        {startTime: 82225412, endTime: 82403992},
        {startTime: 82318006, endTime: 82447677},

        // Here's another batch, taking place after all the others:
        {startTime: 82467775, endTime: 82559004},
        {startTime: 82495068, endTime: 82560063},

        // Here's a run that would be in a separate batch, before the others...
        {startTime: 81181571, endTime: 81227100},

        // ...except that this run bridges it together with the first batch
        {startTime: 80172146, endTime: 82195103},
      ];

      const batched = batchRunsForTimeline({
        runs,
        start: 80000000,
        end: 82600000,
        width: 1000,
        minChunkWidth,
        minMultipleWidth,
      });

      expect(batched.length).toBe(2);
    });
  });
});
