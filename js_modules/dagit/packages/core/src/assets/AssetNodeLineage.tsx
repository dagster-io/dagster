import {
  Box,
  Button,
  ButtonGroup,
  Checkbox,
  Colors,
  Icon,
  JoinedButtons,
  TextInput,
} from '@dagster-io/ui';
import * as React from 'react';

import {GraphData, LiveData} from '../asset-graph/Utils';
import {AssetGraphQueryItem, calculateGraphDistances} from '../asset-graph/useAssetGraphData';

import {AssetLineageScope, AssetNodeLineageGraph} from './AssetNodeLineageGraph';
import {AssetViewParams} from './AssetView';
import {LaunchAssetExecutionButton} from './LaunchAssetExecutionButton';
import {AssetNodeDefinitionFragment} from './types/AssetNodeDefinitionFragment';

export const AssetNodeLineage: React.FC<{
  params: AssetViewParams;
  setParams: (params: AssetViewParams) => void;
  assetNode: AssetNodeDefinitionFragment;
  assetGraphData: GraphData;
  liveDataByNode: LiveData;
  requestedDepth: number;
  graphQueryItems: AssetGraphQueryItem[];
}> = ({
  params,
  setParams,
  assetNode,
  liveDataByNode,
  assetGraphData,
  graphQueryItems,
  requestedDepth,
}) => {
  const maxDistances = React.useMemo(
    () => calculateGraphDistances(graphQueryItems, assetNode.assetKey),
    [graphQueryItems, assetNode],
  );
  const maxDepth =
    params.lineageScope === 'upstream'
      ? maxDistances.upstream
      : params.lineageScope === 'downstream'
      ? maxDistances.downstream
      : Math.max(maxDistances.upstream, maxDistances.downstream);

  return (
    <>
      <Box
        flex={{justifyContent: 'space-between', alignItems: 'center', gap: 12}}
        padding={{left: 24, right: 12, vertical: 12}}
        border={{side: 'bottom', color: Colors.KeylineGray, width: 1}}
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
          value={Math.max(1, Math.min(maxDepth, requestedDepth))}
          onChange={(depth) => setParams({...params, lineageDepth: depth})}
          max={maxDepth}
        />
        <Checkbox
          format="switch"
          label="Include secondary edges"
          checked={!!params.lineageShowSecondaryEdges}
          onChange={() =>
            setParams({
              ...params,
              lineageShowSecondaryEdges: params.lineageShowSecondaryEdges ? undefined : true,
            })
          }
        />
        <div style={{flex: 1}} />
        {Object.values(assetGraphData.nodes).length > 1 ? (
          <LaunchAssetExecutionButton
            assetKeys={Object.values(assetGraphData.nodes).map((n) => n.assetKey)}
            intent="none"
            context="all"
          />
        ) : (
          <Button icon={<Icon name="materialization" />} disabled>
            Materialize all
          </Button>
        )}
      </Box>
      <AssetNodeLineageGraph
        assetNode={assetNode}
        liveDataByNode={liveDataByNode}
        assetGraphData={assetGraphData}
        params={params}
      />
    </>
  );
};

const LineageDepthControl: React.FC<{
  value: number;
  max: number;
  onChange: (v: number) => void;
}> = ({value, max, onChange}) => {
  const [text, setText] = React.useState(`${value}`);
  React.useEffect(() => {
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
      <JoinedButtons>
        <Button
          disabled={value <= 1}
          onClick={() => onChange(value - 1)}
          icon={<Icon name="arrow_back" />}
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
            border: `1px solid ${Colors.Gray300}`,
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
          icon={<Icon name="arrow_forward" />}
        />
        <Button disabled={value >= max} onClick={() => onChange(max)}>
          All
        </Button>
      </JoinedButtons>
      Graph depth
    </Box>
  );
};
