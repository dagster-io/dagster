import {
  Box,
  Button,
  ButtonGroup,
  Colors,
  Icon,
  JoinedButtons,
  MenuItem,
  Suggest,
  TextInput,
} from '@dagster-io/ui-components';
import React, {useEffect, useMemo, useState} from 'react';
import styled from 'styled-components';

import {AssetColumnLineageGraph} from './AssetColumnLineageGraph';
import {AssetNodeLineageGraph} from './AssetNodeLineageGraph';
import {LaunchAssetExecutionButton} from './LaunchAssetExecutionButton';
import {asAssetKeyInput} from './asInput';
import {useColumnLineageDataForAssets} from './lineage/useColumnLineageDataForAssets';
import {AssetLineageScope, AssetViewParams} from './types';
import {GraphData, toGraphId} from '../asset-graph/Utils';
import {AssetGraphQueryItem, calculateGraphDistances} from '../asset-graph/useAssetGraphData';
import {AssetKeyInput} from '../graphql/types';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {ClearButton} from '../ui/ClearButton';

export const AssetNodeLineage = ({
  params,
  setParams,
  assetKey,
  assetGraphData,
  graphQueryItems,
  requestedDepth,
}: {
  params: AssetViewParams;
  setParams: (params: AssetViewParams) => void;
  assetKey: AssetKeyInput;
  assetGraphData: GraphData;
  requestedDepth: number;
  graphQueryItems: AssetGraphQueryItem[];
}) => {
  const maxDistances = useMemo(
    () => calculateGraphDistances(graphQueryItems, assetKey),
    [graphQueryItems, assetKey],
  );
  const maxDepth =
    params.lineageScope === 'upstream'
      ? maxDistances.upstream
      : params.lineageScope === 'downstream'
      ? maxDistances.downstream
      : Math.max(maxDistances.upstream, maxDistances.downstream);

  const currentDepth = Math.max(1, Math.min(maxDepth, requestedDepth));

  const assetGraphKeys = useMemo(
    () => Object.values(assetGraphData.nodes).map(asAssetKeyInput),
    [assetGraphData],
  );
  const columnLineageData = useColumnLineageDataForAssets(assetGraphKeys);
  const columnLineage = columnLineageData[toGraphId(assetKey)];
  const [column, setColumn] = useQueryPersistedState<string | null>({
    queryKey: 'column',
    decode: (qs) => qs.column || null,
    encode: (column) => ({column: column || undefined}),
  });

  return (
    <Box
      style={{width: '100%', flex: 1, minHeight: 0, position: 'relative'}}
      flex={{direction: 'column'}}
    >
      <Box
        flex={{justifyContent: 'space-between', alignItems: 'center', gap: 12}}
        padding={{left: 24, right: 12, vertical: 12}}
        border="bottom"
      >
        <ButtonGroup<AssetLineageScope>
          activeItems={new Set([params.lineageScope || 'neighbors'])}
          buttons={[
            {id: 'neighbors', label: 'Nearest Neighbors', icon: 'graph_neighbors'},
            {id: 'upstream', label: 'Upstream', icon: 'graph_upstream'},
            {id: 'downstream', label: 'Downstream', icon: 'graph_downstream'},
          ]}
          onClick={(lineageScope) => setParams({...params, lineageScope, lineageDepth: undefined})}
        />
        <LineageDepthControl
          value={currentDepth}
          onChange={(depth) => setParams({...params, lineageDepth: depth})}
          max={maxDepth}
        />
        {columnLineage || column ? (
          <>
            Column
            <Suggest
              resetOnQuery={false}
              resetOnClose={false}
              resetOnSelect={false}
              inputProps={{
                placeholder: 'Select a column…',
                rightElement: column ? (
                  <ClearButton
                    onClick={() => setColumn(null)}
                    style={{marginTop: 5, marginRight: 4}}
                  >
                    <Icon name="cancel" />
                  </ClearButton>
                ) : undefined,
              }}
              selectedItem={column}
              items={Object.keys(columnLineage || {})}
              noResults="No matching columns"
              onItemSelect={setColumn}
              inputValueRenderer={(item) => item}
              itemPredicate={(query, item) =>
                item.toLocaleLowerCase().includes(query.toLocaleLowerCase())
              }
              itemRenderer={(item, itemProps) => (
                <MenuItem
                  active={itemProps.modifiers.active}
                  onClick={(e) => itemProps.handleClick(e)}
                  text={item}
                  key={item}
                />
              )}
            />
          </>
        ) : undefined}
        <div style={{flex: 1}} />
        {Object.values(assetGraphData.nodes).length > 1 ? (
          <LaunchAssetExecutionButton
            primary={false}
            scope={{all: Object.values(assetGraphData.nodes).map((n) => n.definition)}}
          />
        ) : (
          <Button icon={<Icon name="materialization" />} disabled>
            Materialize all
          </Button>
        )}
      </Box>
      {currentDepth < maxDepth && (
        <DepthHidesAssetsNotice>
          Not all upstream/downstream assets shown. Increase the depth to show more.
        </DepthHidesAssetsNotice>
      )}
      {column ? (
        <AssetColumnLineageGraph
          assetKey={assetKey}
          assetGraphData={assetGraphData}
          columnLineageData={columnLineageData}
          focusedColumn={column}
        />
      ) : (
        <AssetNodeLineageGraph
          assetKey={assetKey}
          assetGraphData={assetGraphData}
          params={params}
        />
      )}
    </Box>
  );
};

const DepthHidesAssetsNotice = styled.div`
  background: ${Colors.backgroundLight()};
  border-radius: 8px;
  color: ${Colors.textLight()};
  align-items: center;
  display: flex;
  padding: 4px 8px;
  gap: 4px;
  position: absolute;
  right: 12px;
  top: 70px;
  z-index: 2;
`;

const LineageDepthControl = ({
  value,
  max,
  onChange,
}: {
  value: number;
  max: number;
  onChange: (v: number) => void;
}) => {
  const [text, setText] = useState(`${value}`);
  useEffect(() => {
    setText(`${value}`);
  }, [value]);

  // We maintain the value in a separate piece of state so the user can clear it
  // or briefly have an invalid value, and also so that the graph doesn't re-render
  // on each keystroke which could be expensive.
  const commitText = () => {
    const next = Number(text) ? Math.min(max, Number(text)) : value;
    onChange(next);
  };

  return (
    <Box flex={{gap: 8, alignItems: 'center'}}>
      Graph depth
      <JoinedButtons>
        <Button
          disabled={value <= 1}
          onClick={() => onChange(value - 1)}
          icon={<Icon name="dash" />}
        />
        <TextInput
          min={1}
          max={max}
          disabled={max <= 1}
          inputMode="numeric"
          style={{
            width: 40,
            marginLeft: -1,
            textAlign: 'center',
            height: 32,
            padding: 6,
            borderRadius: 0,
            boxShadow: 'none',
            border: `1px solid ${Colors.borderDefault()}`,
          }}
          key={value}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => (e.key === 'Enter' || e.key === 'Return' ? commitText() : undefined)}
          onBlur={() => commitText()}
        />
        <Button
          disabled={value >= max}
          onClick={() => onChange(value + 1)}
          icon={<Icon name="add" />}
        />
        <Button disabled={value >= max} onClick={() => onChange(max)}>
          All
        </Button>
      </JoinedButtons>
    </Box>
  );
};
