import {
  Box,
  Button,
  Dialog,
  DialogFooter,
  Icon,
  MenuItem,
  Mono,
  NonIdealState,
  Select,
  SpinnerWithText,
  Tab,
  Tabs,
  Tag,
} from '@dagster-io/ui-components';
import {ReactNode, useEffect, useMemo, useState} from 'react';

import {GET_SLIM_EVALUATIONS_QUERY} from './GetEvaluationsQuery';
import {PartitionTagSelector} from './PartitionTagSelector';
import {QueryfulEvaluationDetailTable} from './QueryfulEvaluationDetailTable';
import {runTableFiltersForEvaluation} from './runTableFiltersForEvaluation';
import {
  GetSlimEvaluationsQuery,
  GetSlimEvaluationsQueryVariables,
} from './types/GetEvaluationsQuery.types';
import {usePartitionsForAssetKey} from './usePartitionsForAssetKey';
import {useQuery} from '../../apollo-client';
import {DEFAULT_TIME_FORMAT} from '../../app/time/TimestampFormat';
import {displayNameForAssetKey, tokenForAssetKey} from '../../asset-graph/Utils';
import {RunsFeedTableWithFilters} from '../../runs/RunsFeedTable';
import {TimestampDisplay} from '../../schedules/TimestampDisplay';
import {AnchorButton} from '../../ui/AnchorButton';
import {AssetKey} from '../types';

export type Tab = 'evaluation' | 'runs';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  assetKeyPath: string[];
  assetCheckName?: string;
  evaluationID: string;
  initialTab?: Tab;
}

export const EvaluationDetailDialog = ({
  isOpen,
  onClose,
  evaluationID,
  assetKeyPath,
  assetCheckName,
  initialTab = 'evaluation',
}: Props) => {
  return (
    <Dialog isOpen={isOpen} onClose={onClose} style={EvaluationDetailDialogStyle}>
      <EvaluationDetailDialogContents
        initialEvaluationID={evaluationID}
        initialAssetKeyPath={assetKeyPath}
        initialAssetCheckName={assetCheckName}
        onClose={onClose}
        initialTab={initialTab}
      />
    </Dialog>
  );
};

interface ContentProps {
  initialEvaluationID: string;
  initialAssetKeyPath: string[];
  initialAssetCheckName?: string;
  onClose: () => void;
  initialTab?: Tab;
}

const EvaluationDetailDialogContents = ({
  initialEvaluationID,
  initialAssetKeyPath,
  initialAssetCheckName,
  onClose,
  initialTab = 'evaluation',
}: ContentProps) => {
  const [selectedPartition, setSelectedPartition] = useState<string | null>(null);
  const [tabId, setTabId] = useState<Tab>(initialTab);
  const [evaluationID, setEvaluationID] = useState<string>(initialEvaluationID);
  const [assetKeyPath, setAssetKeyPath] = useState<string[]>(initialAssetKeyPath);
  const [assetCheckName, setAssetCheckName] = useState<string | undefined>(initialAssetCheckName);
  useEffect(() => {
    setAssetKeyPath(initialAssetKeyPath);
    setAssetCheckName(initialAssetCheckName);
    setEvaluationID(initialEvaluationID);
  }, [initialEvaluationID, initialAssetKeyPath, initialAssetCheckName]);

  const {data, loading} = useQuery<GetSlimEvaluationsQuery, GetSlimEvaluationsQueryVariables>(
    GET_SLIM_EVALUATIONS_QUERY,
    {
      variables: {
        assetKey: assetCheckName ? null : {path: assetKeyPath},
        assetCheckKey: assetCheckName
          ? {assetKey: {path: assetKeyPath}, name: assetCheckName}
          : null,
        cursor: `${BigInt(evaluationID) + 1n}`,
        limit: 2,
      },
    },
  );

  const {partitions: allPartitions, loading: partitionsLoading} =
    usePartitionsForAssetKey(assetKeyPath);

  const viewAllPath = useMemo(() => {
    // todo dish: I don't think the asset check evaluations list is permalinkable yet.
    if (assetCheckName) {
      return null;
    }

    const queryString = new URLSearchParams({
      view: 'automation',
      evaluation: evaluationID,
    }).toString();

    return `/assets/${assetKeyPath.join('/')}?${queryString}`;
  }, [assetCheckName, evaluationID, assetKeyPath]);

  if (loading || partitionsLoading) {
    return (
      <DialogContents
        header={<DialogHeader assetKeyPath={assetKeyPath} assetCheckName={assetCheckName} />}
        selectedTabId={tabId}
        onTabChange={setTabId}
        body={
          <Box padding={{top: 64}} flex={{direction: 'row', justifyContent: 'center'}}>
            <SpinnerWithText label="Loading evaluation details..." />
          </Box>
        }
        onDone={onClose}
      />
    );
  }

  const record = data?.assetConditionEvaluationRecordsOrError;

  if (record?.__typename === 'AutoMaterializeAssetEvaluationNeedsMigrationError') {
    return (
      <DialogContents
        header={<DialogHeader assetKeyPath={assetKeyPath} assetCheckName={assetCheckName} />}
        selectedTabId={tabId}
        onTabChange={setTabId}
        body={
          <Box margin={{top: 64}}>
            <NonIdealState
              icon="automation"
              title="Evaluation needs migration"
              description={record.message}
            />
          </Box>
        }
        onDone={onClose}
      />
    );
  }

  const evaluation = record?.records.find((r) => r.evaluationId === evaluationID);

  if (!evaluation) {
    return (
      <DialogContents
        header={<DialogHeader assetKeyPath={assetKeyPath} assetCheckName={assetCheckName} />}
        selectedTabId={tabId}
        onTabChange={setTabId}
        onDone={onClose}
        body={
          <Box margin={{top: 64}}>
            <NonIdealState
              icon="automation"
              title="Evaluation not found"
              description={
                <>
                  Evaluation <Mono>{evaluationID}</Mono> not found
                </>
              }
            />
          </Box>
        }
      />
    );
  }

  const {runIds, upstreamAssetKeys, downstreamAssetKeys} = evaluation;

  const body = () => {
    if (tabId === 'evaluation') {
      return (
        <QueryfulEvaluationDetailTable
          evaluation={evaluation}
          assetKeyPath={assetKeyPath}
          selectedPartition={selectedPartition}
          setSelectedPartition={setSelectedPartition}
          onEntityChange={({
            assetKeyPath,
            assetCheckName,
            evaluationId: newEvaluationId,
          }: {
            assetKeyPath: string[];
            assetCheckName: string | undefined;
            evaluationId?: string;
          }) => {
            setAssetKeyPath(assetKeyPath);
            setAssetCheckName(assetCheckName);
            if (newEvaluationId && newEvaluationId !== evaluationID) {
              setEvaluationID(newEvaluationId);
            }
          }}
        />
      );
    }

    const filter = runTableFiltersForEvaluation(evaluation.runIds);
    if (filter) {
      return <RunsFeedTableWithFilters filter={filter} includeRunsFromBackfills={false} />;
    }

    return (
      <Box padding={{top: 64}} flex={{direction: 'row', justifyContent: 'center'}}>
        <NonIdealState
          icon="run"
          title="No runs launched"
          description="No runs were launched by this evaluation."
        />
      </Box>
    );
  };

  const onAssetSelect = (assetKey: AssetKey) => {
    setAssetKeyPath(assetKey.path);
    setAssetCheckName(undefined);
  };
  return (
    <DialogContents
      onTabChange={setTabId}
      runCount={runIds.length}
      selectedTabId={tabId}
      onDone={onClose}
      header={
        <DialogHeader
          assetKeyPath={assetKeyPath}
          assetCheckName={assetCheckName}
          timestamp={evaluation.timestamp}
          upstreamAssetKeys={upstreamAssetKeys}
          downstreamAssetKeys={downstreamAssetKeys}
          onAssetSelect={onAssetSelect}
        />
      }
      rightOfTabs={
        allPartitions.length > 0 && evaluation.isLegacy ? (
          <Box padding={{vertical: 12}} flex={{justifyContent: 'flex-end'}}>
            <PartitionTagSelector
              allPartitions={allPartitions}
              selectedPartition={selectedPartition}
              selectPartition={setSelectedPartition}
            />
          </Box>
        ) : null
      }
      body={body()}
      viewAllButton={
        viewAllPath ? (
          <AnchorButton to={viewAllPath} icon={<Icon name="automation_condition" />}>
            View evaluations for this asset
          </AnchorButton>
        ) : null
      }
    />
  );
};

const DialogHeader = ({
  assetKeyPath,
  assetCheckName,
  timestamp,
  upstreamAssetKeys,
  downstreamAssetKeys,
  onAssetSelect,
}: {
  assetKeyPath: string[];
  assetCheckName?: string;
  timestamp?: number;
  upstreamAssetKeys?: AssetKey[];
  downstreamAssetKeys?: AssetKey[];
  onAssetSelect?: (assetKey: AssetKey) => void;
}) => {
  const assetKeyPathString = assetKeyPath.join('/');
  const assetDetailsTag = assetCheckName ? (
    <Tag icon="asset_check">
      {assetCheckName} on {assetKeyPathString}
    </Tag>
  ) : (
    <Tag icon="asset">{assetKeyPathString}</Tag>
  );

  const timestampDisplay = timestamp ? (
    <TimestampDisplay
      timestamp={timestamp}
      timeFormat={{...DEFAULT_TIME_FORMAT, showSeconds: true}}
    />
  ) : null;

  const evaluationDetails = (
    <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
      <Icon name="automation" />
      <strong>
        <span>Evaluation details</span>
        {timestampDisplay ? <span>: {timestampDisplay}</span> : ''}
      </strong>
    </Box>
  );

  const canNavigateLineage =
    !!onAssetSelect && (upstreamAssetKeys?.length || downstreamAssetKeys?.length);
  const upstreamSelector = canNavigateLineage ? (
    <AssetSelector label="Upstream" assetKeys={upstreamAssetKeys || []} onSelect={onAssetSelect} />
  ) : null;
  const downstreamSelector = canNavigateLineage ? (
    <AssetSelector
      label="Downstream"
      assetKeys={downstreamAssetKeys || []}
      onSelect={onAssetSelect}
    />
  ) : null;
  if (canNavigateLineage) {
    return (
      <div>
        <Box padding={{top: 16}} flex={{direction: 'row', justifyContent: 'center'}}>
          {evaluationDetails}
        </Box>
        <Box
          padding={{vertical: 16, horizontal: 20}}
          flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
          border="bottom"
        >
          <div>{upstreamSelector}</div>
          {assetDetailsTag}
          <div>{downstreamSelector}</div>
        </Box>
      </div>
    );
  } else {
    return (
      <Box
        padding={{vertical: 16, horizontal: 20}}
        flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
        border="bottom"
      >
        {evaluationDetails}
        {assetDetailsTag}
      </Box>
    );
  }
};

const AssetSelector = ({
  label,
  assetKeys,
  onSelect,
}: {
  label: string;
  assetKeys: AssetKey[];
  onSelect: (assetKey: AssetKey) => void;
}) => {
  return (
    <Select<AssetKey>
      disabled={!assetKeys.length}
      items={assetKeys}
      itemRenderer={(item, props) => (
        <MenuItem
          key={tokenForAssetKey(item)}
          icon="asset"
          text={displayNameForAssetKey(item)}
          onClick={props.handleClick}
        />
      )}
      onItemSelect={onSelect}
      filterable={false}
    >
      <Button
        icon={<Icon name="asset" />}
        rightIcon={<Icon name="arrow_drop_down" />}
        disabled={!assetKeys.length}
      >
        {label}
      </Button>
    </Select>
  );
};

interface BasicContentProps {
  header: ReactNode;
  body: ReactNode;
  rightOfTabs?: ReactNode;
  viewAllButton?: ReactNode;
  selectedTabId: Tab;
  onTabChange: (tabId: Tab) => void;
  onDone: () => void;
  runCount?: number;
}

// Dialog contents for which the body container is scrollable and expands to fill the height.
const DialogContents = ({
  header,
  body,
  selectedTabId,
  onTabChange,
  rightOfTabs,
  runCount = 0,
  viewAllButton,
  onDone,
}: BasicContentProps) => {
  return (
    <Box flex={{direction: 'column'}} style={{height: '100%'}}>
      {header}
      <Box
        padding={{horizontal: 20}}
        border="bottom"
        flex={{direction: 'row', justifyContent: 'space-between'}}
      >
        <Tabs selectedTabId={selectedTabId} onChange={onTabChange}>
          <Tab id="evaluation" title="Evaluation" />
          <Tab
            id="runs"
            title={
              runCount > 0 ? (
                <span>
                  Runs <span style={{fontVariantNumeric: 'tabular-nums'}}>({runCount})</span>
                </span>
              ) : (
                'Runs'
              )
            }
            disabled={runCount === 0}
          />
        </Tabs>
        {rightOfTabs}
      </Box>
      <div style={{flex: 1, overflowY: 'auto'}}>{body}</div>
      <div style={{flexGrow: 0}}>
        <DialogFooter topBorder left={viewAllButton}>
          <Button onClick={onDone}>Done</Button>
        </DialogFooter>
      </div>
    </Box>
  );
};

const EvaluationDetailDialogStyle = {
  width: '80vw',
  maxWidth: '1400px',
  minWidth: '800px',
  height: '80vh',
  minHeight: '400px',
  maxHeight: '1400px',
};
