import {Box, Container, Inner, Row, Viewport, useViewport} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import React, {useMemo, useRef} from 'react';

import {TILE_GAP} from './AssetSelectionSummaryTile';
import {useSectionToggle} from '../../hooks/useSectionToggle';

export type Sections<T> = {
  items: T[];
  id: string;
  renderSectionHeader: ({
    isOpen,
    toggleOpen,
  }: {
    isOpen: boolean;
    toggleOpen: () => void;
  }) => React.ReactNode;
  renderItem: (item: T, index: number) => React.ReactNode;
  renderTile: (item: T, index: number) => React.ReactNode;
}[];

const PADDING_HORIZONTAL = 24;

function getSectionRows<T>(params: {
  sections: Sections<T>;
  closedSectionsSet: Set<string>;
  toggleSection: (id: string) => void;
  renderType: 'tile' | 'item';
  tileGap?: number;
  tileWidth?: number;
  viewport?: Viewport;
}): React.ReactNode[] {
  const {sections, closedSectionsSet, toggleSection, renderType, tileGap, tileWidth, viewport} =
    params;
  return sections.flatMap(({items, renderTile, renderItem, renderSectionHeader, id}) => {
    const isOpen = !closedSectionsSet.has(id);
    const header = renderSectionHeader({
      isOpen,
      toggleOpen: () => toggleSection(id),
    });
    if (
      renderType === 'tile' &&
      isOpen &&
      viewport &&
      tileGap !== undefined &&
      tileWidth !== undefined
    ) {
      const tiles = items.map((item, index) => renderTile(item, index));
      const tilesPerRow = getTilesPerRow(viewport, tileGap, tileWidth);
      const rowCount = Math.ceil(tiles.length / tilesPerRow);
      return [
        header,
        ...Array.from({length: rowCount}, (_, i) => (
          <Box
            key={i}
            padding={{
              horizontal: PADDING_HORIZONTAL,
              bottom: tileGap as any,
            }}
            style={{
              rowGap: tileGap,
              columnGap: tileGap,
              display: 'grid',
              gridTemplateColumns: `repeat(${tilesPerRow}, minmax(0, 1fr))`,
            }}
          >
            {tiles.slice(i * tilesPerRow, (i + 1) * tilesPerRow)}
          </Box>
        )),
      ];
    } else if (renderType === 'item' && isOpen) {
      return [header, ...items.map((item, index) => renderItem(item, index))];
    } else {
      return [header];
    }
  });
}

export const SectionedGrid = <T,>({
  sections,
  tileGap,
  tileWidth,
}: {
  sections: Sections<T>;
  tileGap: number;
  tileWidth: number;
}) => {
  const {viewport, containerProps} = useViewport();
  const {closedSectionsSet, toggleSection} = useSectionToggle('closed-sections');
  const rows = useMemo(
    () =>
      viewport.width
        ? getSectionRows({
            sections,
            closedSectionsSet,
            toggleSection,
            renderType: 'tile',
            tileGap,
            tileWidth,
            viewport,
          })
        : [],
    [sections, closedSectionsSet, toggleSection, viewport, tileGap, tileWidth],
  );

  return (
    <div {...containerProps}>
      <List rows={rows} />
    </div>
  );
};

export const SectionedList = <T,>({sections}: {sections: Sections<T>}) => {
  const {closedSectionsSet, toggleSection} = useSectionToggle('closed-sections');
  const rows = useMemo(
    () =>
      getSectionRows({
        sections,
        closedSectionsSet,
        toggleSection,
        renderType: 'item',
      }),
    [sections, closedSectionsSet, toggleSection],
  );

  return <List rows={rows} />;
};

export const Grid = ({
  tiles,
  tileGap,
  tileWidth,
}: {
  tiles: React.ReactNode[];
  tileGap: number;
  tileWidth: number;
}) => {
  const {viewport, containerProps} = useViewport();

  const rows = useMemo(() => {
    if (!viewport.width) {
      return [];
    }
    return getSectionRows({
      sections: [
        {
          items: tiles,
          id: 'grid',
          renderSectionHeader: () => <div style={{height: TILE_GAP}} />,
          renderItem: (item) => item,
          renderTile: (item) => item,
        },
      ],
      closedSectionsSet: new Set(),
      toggleSection: () => {},
      renderType: 'tile',
      tileGap,
      tileWidth,
      viewport,
    });
  }, [tiles, viewport, tileGap, tileWidth]);

  return (
    <div {...containerProps}>
      <List rows={rows} />
    </div>
  );
};

export function getTilesPerRow(viewport: Viewport, tileGap: number, tileWidth: number) {
  if (!viewport.width) {
    return 0;
  }
  return Math.max(
    Math.floor((viewport.width + tileGap - PADDING_HORIZONTAL * 2) / (tileWidth + tileGap)),
    1,
  );
}

export const List = ({rows}: {rows: React.ReactNode[]}) => {
  const scrollWrapperRef = useRef<HTMLDivElement | null>(null);
  const rowVirtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => scrollWrapperRef.current,
    estimateSize: () => 28,
    overscan: 0,
  });

  const rowItems = rowVirtualizer.getVirtualItems();
  const totalHeight = rowVirtualizer.getTotalSize();

  return (
    <Container ref={scrollWrapperRef} style={{maxHeight: '600px', overflowY: 'auto'}}>
      <Inner $totalHeight={totalHeight}>
        {rowItems.map(({index, key, size, start}) => {
          // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
          const row = rows[index]!;
          return (
            <Row key={key} $height={size} $start={start}>
              <div ref={rowVirtualizer.measureElement} data-index={index}>
                {row}
              </div>
            </Row>
          );
        })}
      </Inner>
    </Container>
  );
};
