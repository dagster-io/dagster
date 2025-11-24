import {PartitionDefinitionType} from '../../graphql/types';
import {DimensionQueryState, buildSerializer} from '../usePartitionDimensionSelections';

describe('usePartitionDimensionSelections', () => {
  describe('buildSerializer', () => {
    it('should encode', () => {
      const state: DimensionQueryState[] = [
        {
          name: 'default',
          rangeText: '2025-11-13',
          isFromPartitionQueryStringParam: false,
        },
      ];

      const {encode} = buildSerializer({dimensions: []});
      if (!encode) {
        throw new Error('encode is undefined');
      }

      expect(encode(state)).toEqual({
        default_range: '2025-11-13',
      });
    });

    it('should encode multiple dimensions', () => {
      const state: DimensionQueryState[] = [
        {
          name: 'default',
          rangeText: '2025-11-13',
          isFromPartitionQueryStringParam: false,
        },
        {
          name: 'secondary',
          rangeText: '2025-11-14',
          isFromPartitionQueryStringParam: false,
        },
      ];

      const {encode} = buildSerializer({dimensions: []});
      if (!encode) {
        throw new Error('encode is undefined');
      }

      expect(encode(state)).toEqual({
        default_range: '2025-11-13',
        secondary_range: '2025-11-14',
      });
    });

    it('should decode one dimension, just range', () => {
      const dimensions = [
        {
          name: 'default',
          type: PartitionDefinitionType.STATIC,
          partitionKeys: ['2025-11-12', '2025-11-13'],
        },
      ];

      const {decode} = buildSerializer({dimensions});
      if (!decode) {
        throw new Error('decode is undefined');
      }

      expect(decode({default_range: '2025-11-13'})).toEqual([
        {name: 'default', rangeText: '2025-11-13', isFromPartitionQueryStringParam: false},
      ]);
    });

    it('should decode one dimension, range and partition params', () => {
      const dimensions = [
        {
          name: 'default',
          type: PartitionDefinitionType.STATIC,
          partitionKeys: ['2025-11-12', '2025-11-13'],
        },
      ];

      const {decode} = buildSerializer({dimensions});
      if (!decode) {
        throw new Error('decode is undefined');
      }

      expect(decode({default_range: '2025-11-13', partition: '2025-11-12'})).toEqual([
        {name: 'default', rangeText: '2025-11-13', isFromPartitionQueryStringParam: false},
      ]);
    });

    it('should decode one dimension, reverse order of params, range and partition params', () => {
      const dimensions = [
        {
          name: 'default',
          type: PartitionDefinitionType.STATIC,
          partitionKeys: ['2025-11-12', '2025-11-13'],
        },
      ];

      const {decode} = buildSerializer({dimensions});
      if (!decode) {
        throw new Error('decode is undefined');
      }

      expect(decode({partition: '2025-11-12', default_range: '2025-11-13'})).toEqual([
        {name: 'default', rangeText: '2025-11-13', isFromPartitionQueryStringParam: false},
      ]);
    });

    it('should decode one dimension, partition params', () => {
      const dimensions = [
        {
          name: 'default',
          type: PartitionDefinitionType.STATIC,
          partitionKeys: ['2025-11-12', '2025-11-13'],
        },
      ];

      const {decode} = buildSerializer({dimensions});
      if (!decode) {
        throw new Error('decode is undefined');
      }

      expect(decode({partition: '2025-11-12'})).toEqual([
        {name: 'default', rangeText: '2025-11-12', isFromPartitionQueryStringParam: true},
      ]);
    });

    it('should decode multiple dimensions, partition params', () => {
      const dimensions = [
        {
          name: 'default',
          type: PartitionDefinitionType.STATIC,
          partitionKeys: ['2025-11-12', '2025-11-13'],
        },
        {
          name: 'secondary',
          type: PartitionDefinitionType.STATIC,
          partitionKeys: ['2025-11-14', '2025-11-15'],
        },
      ];

      const {decode} = buildSerializer({dimensions});
      if (!decode) {
        throw new Error('decode is undefined');
      }

      expect(decode({partition: '2025-11-12|2025-11-14'})).toEqual([
        {name: 'default', rangeText: '2025-11-12', isFromPartitionQueryStringParam: true},
        {name: 'secondary', rangeText: '2025-11-14', isFromPartitionQueryStringParam: true},
      ]);
    });
  });
});
