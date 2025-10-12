import {Box, Button, Icon, TextInput} from '@dagster-io/ui-components';
import * as React from 'react';

import {useStateWithStorage} from '../hooks/useStateWithStorage';

export const CustomKindIconMappingStorageKey = 'CustomKindIconMapping';

export type KindIconMapping = {
  kind: string;
  svg_url: string;
};

function isKindIconMappingArray(data: unknown): data is KindIconMapping[] {
  if (!Array.isArray(data)) {
    return false;
  }

  return data.every((item) => {
    return (
      typeof item === 'object' &&
      item !== null &&
      'kind' in item &&
      typeof (item as any).kind === 'string' &&
      'svg_url' in item &&
      typeof (item as any).svg_url === 'string'
    );
  });
}

const DEFAULT_MAPPING: KindIconMapping[] = [{kind: '', svg_url: ''}];

export const CustomKindIconMappingContext = React.createContext<
  ReturnType<typeof useStateWithStorage<KindIconMapping[]>>
>([DEFAULT_MAPPING, () => [], () => {}]);

export const CustomKindIconMappingProvider = ({children}: {children: React.ReactNode}) => {
  const state = useStateWithStorage<KindIconMapping[]>(CustomKindIconMappingStorageKey, (json) =>
    isKindIconMappingArray(json) ? json : DEFAULT_MAPPING,
  );

  return (
    <CustomKindIconMappingContext.Provider value={state}>
      {children}
    </CustomKindIconMappingContext.Provider>
  );
};

export const CustomKindIconMappingEditor = ({}) => {
  const [kindIconMapping, setKindIconMapping] = React.useContext(CustomKindIconMappingContext);

  const onMappingEdit = (kind: string, svg_url: string, idx: number) => {
    setKindIconMapping([
      ...kindIconMapping.slice(0, idx),
      {kind, svg_url},
      ...kindIconMapping.slice(idx + 1),
    ]);
  };

  const onRemove = (idx: number) => {
    if (idx === 0 && kindIconMapping.length === 1) {
      setKindIconMapping([{kind: '', svg_url: ''}]);
    } else {
      setKindIconMapping([...kindIconMapping.slice(0, idx), ...kindIconMapping.slice(idx + 1)]);
    }
  };

  const addMappingEntry = () => {
    setKindIconMapping([...kindIconMapping, {kind: '', svg_url: ''}]);
  };

  return (
    <Box flex={{direction: 'column', gap: 12}}>
      <Box flex={{direction: 'column', gap: 8}}>
        {kindIconMapping.map((mapping, idx) => {
          const {kind, svg_url} = mapping;
          return (
            <div
              key={idx}
              style={{
                display: 'flex',
                flexDirection: 'row',
                gap: 8,
              }}
            >
              <TextInput
                placeholder="Kind"
                value={kind}
                fill
                style={{width: '100%'}}
                onChange={(e) => onMappingEdit(e.target.value, svg_url, idx)}
              />
              <TextInput
                placeholder="SVG Url"
                value={svg_url}
                fill
                style={{width: '100%'}}
                onChange={(e) => onMappingEdit(kind, e.target.value, idx)}
              />
              <Button
                disabled={kindIconMapping.length === 1 && !kind.trim() && !svg_url.trim()}
                onClick={() => onRemove(idx)}
                icon={<Icon name="delete" />}
              />
            </div>
          );
        })}
      </Box>
      <Box margin={{left: 2}} flex={{direction: 'row'}}>
        <Button onClick={addMappingEntry} icon={<Icon name="add_circle" />}>
          Add custom kind icon
        </Button>
      </Box>
    </Box>
  );
};
