import {renderHook} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';

import {useAssetViewParams} from '../useAssetViewParams';

describe('useAssetViewParams', () => {
  it('supports boolean partition names', () => {
    const {result} = renderHook(() => useAssetViewParams(), {
      wrapper: ({children}) => (
        <MemoryRouter
          initialEntries={[
            '/assets/boolean_partitioned?view=partitions&partition=true&status=MATERIALIZED%2CMATERIALIZING%2CMISSING',
          ]}
        >
          {children}
        </MemoryRouter>
      ),
    });

    expect(result.current[0]).toEqual({
      partition: 'true',
      status: 'MATERIALIZED,MATERIALIZING,MISSING',
      view: 'partitions',
    });
  });

  it('provides numeric lineage depth and showAllEvents using the correct data types', () => {
    const {result} = renderHook(() => useAssetViewParams(), {
      wrapper: ({children}) => (
        <MemoryRouter
          initialEntries={[
            '/assets/boolean_partitioned?showAllEvents=true&view=lineage&lineageDepth=2&lineageScope=downstream',
          ]}
        >
          {children}
        </MemoryRouter>
      ),
    });

    expect(result.current[0]).toEqual({
      lineageDepth: 2,
      lineageScope: 'downstream',
      showAllEvents: true,
      view: 'lineage',
    });
  });
});
