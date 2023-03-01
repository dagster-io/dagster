import {PartitionState} from '../../partitions/PartitionStatus';
import {mergedRanges, mergedStates} from '../MultipartitioningSupport';
import {Range} from '../usePartitionHealthData';

describe('multipartitioning support', () => {
  describe('mergedStates', () => {
    it('returns SUCCESS_MISSING if SUCCESS and MISSING are both present', () => {
      expect(
        mergedStates([PartitionState.SUCCESS, PartitionState.MISSING, PartitionState.MISSING]),
      ).toEqual(PartitionState.SUCCESS_MISSING);
    });

    it('returns SUCCESS_MISSING if SUCCESS_MISSING is present', () => {
      expect(
        mergedStates([
          PartitionState.SUCCESS_MISSING,
          PartitionState.MISSING,
          PartitionState.MISSING,
        ]),
      ).toEqual(PartitionState.SUCCESS_MISSING);
    });

    it('returns SUCCESS if all states are success', () => {
      expect(
        mergedStates([PartitionState.SUCCESS, PartitionState.SUCCESS, PartitionState.SUCCESS]),
      ).toEqual(PartitionState.SUCCESS);
    });

    it('returns MISSING if all states are missing', () => {
      expect(
        mergedStates([PartitionState.MISSING, PartitionState.MISSING, PartitionState.MISSING]),
      ).toEqual(PartitionState.MISSING);
    });
    it('should not modify the input data', () => {
      const input = [
        PartitionState.SUCCESS_MISSING,
        PartitionState.MISSING,
        PartitionState.MISSING,
      ];
      const before = JSON.stringify({input});
      mergedStates(input);
      expect(JSON.stringify({input})).toEqual(before);
    });
  });

  describe('mergedRanges', () => {
    const KEYS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'];
    const A_I: Range = {
      start: {idx: 0, key: 'A'},
      end: {idx: 8, key: 'I'},
      value: PartitionState.SUCCESS,
    };
    const A_I_Partial: Range = {
      ...A_I,
      value: PartitionState.SUCCESS_MISSING,
    };
    const B_E: Range = {
      start: {idx: 1, key: 'B'},
      end: {idx: 4, key: 'E'},
      value: PartitionState.SUCCESS,
    };
    const G_I: Range = {
      start: {idx: 6, key: 'G'},
      end: {idx: 8, key: 'I'},
      value: PartitionState.SUCCESS,
    };

    it('merges two [A...I] range set into one [A...I] range set', () => {
      expect(mergedRanges(KEYS, [[A_I], [A_I]])).toEqual([A_I]);
    });

    it('merges two [A...I] partial range sets into one [A...I] partial range set', () => {
      expect(mergedRanges(KEYS, [[A_I_Partial], [A_I_Partial]])).toEqual([A_I_Partial]);
    });

    it('does not throw errors if an empty set is passed', () => {
      expect(mergedRanges(KEYS, [])).toEqual([]);
    });

    it('makes no modifications to a single range set', () => {
      expect(mergedRanges(KEYS, [[A_I_Partial]])).toEqual([A_I_Partial]);
      expect(mergedRanges(KEYS, [[A_I]])).toEqual([A_I]);
      expect(mergedRanges(KEYS, [[B_E, G_I]])).toEqual([B_E, G_I]);
    });

    it('merges range sets which overlap', () => {
      expect(mergedRanges(KEYS, [[A_I], [B_E]])).toEqual([
        {
          start: {idx: 0, key: 'A'},
          end: {idx: 0, key: 'A'},
          value: PartitionState.SUCCESS_MISSING,
        },
        {
          start: {idx: 1, key: 'B'},
          end: {idx: 4, key: 'E'},
          value: PartitionState.SUCCESS,
        },
        {
          start: {idx: 5, key: 'F'},
          end: {idx: 8, key: 'I'},
          value: PartitionState.SUCCESS_MISSING,
        },
      ]);
    });

    it('merges range sets with a one-partition "hole"', () => {
      expect(mergedRanges(KEYS, [[A_I], [B_E, G_I]])).toEqual([
        {
          start: {idx: 0, key: 'A'},
          end: {idx: 0, key: 'A'},
          value: PartitionState.SUCCESS_MISSING,
        },
        {
          start: {idx: 1, key: 'B'},
          end: {idx: 4, key: 'E'},
          value: PartitionState.SUCCESS,
        },
        {
          start: {idx: 5, key: 'F'},
          end: {idx: 5, key: 'F'},
          value: PartitionState.SUCCESS_MISSING,
        },
        {
          start: {idx: 6, key: 'G'},
          end: {idx: 8, key: 'I'},
          value: PartitionState.SUCCESS,
        },
      ]);
    });

    it('should not modify the input data', () => {
      const rangeSets = [[A_I], [B_E, G_I]];
      const before = JSON.stringify({KEYS, rangeSets});
      mergedRanges(KEYS, rangeSets);
      expect(JSON.stringify({KEYS, rangeSets})).toEqual(before);
    });
  });
});
