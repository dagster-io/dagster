import {
  Box,
  Button,
  ButtonLink,
  Colors,
  DialogFooter,
  Dialog,
  Group,
  Icon,
  IconWrapper,
  Table,
  Mono,
} from '@dagster-io/ui';
import moment from 'moment';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {Timestamp} from '../app/time/Timestamp';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {MetadataEntry} from '../metadata/MetadataEntry';
import {PipelineReference} from '../pipelines/PipelineReference';
import {RunStatusWithStats} from '../runs/RunStatusDots';
import {linkToRunEvent, titleForRun} from '../runs/RunUtils';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

import {AssetLineageElements} from './AssetLineageElements';
import {AssetEventGroup} from './groupByPartition';
import {AssetMaterializationFragment} from './types/AssetMaterializationFragment';
import {AssetObservationFragment} from './types/AssetObservationFragment';

export const AssetEventsTable: React.FC<{
  hasPartitions: boolean;
  hasLineage: boolean;
  groups: AssetEventGroup[];
  focused?: AssetEventGroup;
  setFocused?: (timestamp: AssetEventGroup | undefined) => void;
}> = ({hasPartitions, hasLineage, groups, focused, setFocused}) => {
  return (
    <Table>
      <thead>
        <tr>
          {hasPartitions && <th style={{minWidth: 100}}>Partition</th>}
          <th style={{minWidth: 150}}>Timestamp</th>
          <th style={{minWidth: 150}}>Job</th>
          <th style={{width: 100}}>Run</th>
        </tr>
      </thead>
      <tbody>
        {groups.map((group) => (
          <React.Fragment key={group.timestamp || group.partition}>
            <HoverableRow
              onClick={(e) => {
                // If you're interacting with something in the row, don't trigger a focus change.
                // Since focus is stored in the URL bar this overwrites any link click navigation.
                // We could alternatively e.preventDefault() on every link but it's easy to forget.
                if (e.target instanceof HTMLElement && e.target.closest('a')) {
                  return;
                }
                setFocused?.(focused !== group ? group : undefined);
              }}
            >
              <EventGroupRow
                group={group}
                hasPartitions={hasPartitions}
                hasLineage={hasLineage}
                isFocused={focused === group}
              />
            </HoverableRow>
            {focused === group ? (
              <MetadataEntriesRow hasLineage={hasLineage} group={group} />
            ) : undefined}
          </React.Fragment>
        ))}
      </tbody>
    </Table>
  );
};

const NoneSpan = () => <span style={{color: Colors.Gray400}}>None</span>;

const MetadataEntriesRow: React.FC<{
  group: AssetEventGroup;
  hasLineage: boolean;
}> = React.memo(({group, hasLineage}) => {
  const {latest, timestamp} = group;
  if (!latest) {
    return <tr></tr>;
  }
  const assetLineage = latest.__typename === 'MaterializationEvent' ? latest.assetLineage : [];

  const observationsAboutLatest =
    latest.__typename === 'MaterializationEvent'
      ? group.all.filter(
          (e) =>
            e.__typename === 'ObservationEvent' && Number(e.timestamp) > Number(latest.timestamp),
        )
      : [];

  return (
    <tr style={{background: Colors.Gray50}}>
      <td colSpan={6} style={{fontSize: 14, padding: 0}}>
        {latest.description && (
          <Box padding={{horizontal: 24, vertical: 12}}>{latest.description}</Box>
        )}
        {latest.metadataEntries.length || hasLineage ? (
          <DetailsTable>
            <tbody>
              {latest.metadataEntries.map((entry) => (
                <tr key={`metadata-${entry.label}`}>
                  <td style={{maxWidth: 300}}>{entry.label}</td>
                  <td>
                    <MetadataEntry entry={entry} expandSmallValues={true} />
                  </td>
                  <td style={{opacity: 0.7}}>{entry.description}</td>
                </tr>
              ))}
              {observationsAboutLatest.map((obs) => (
                <React.Fragment key={obs.timestamp}>
                  {obs.metadataEntries.map((entry) => (
                    <tr key={`metadata-${obs.timestamp}-${entry.label}`}>
                      <td>{entry.label}</td>
                      <td>
                        <MetadataEntry entry={entry} expandSmallValues={true} />
                      </td>
                      <td style={{opacity: 0.7}}>
                        <Box flex={{gap: 8, alignItems: 'center'}}>
                          <Icon name="observation" size={16} />
                          <span>
                            {`${obs.stepKey} in `}
                            <Link to={`/instance/runs/${obs.runId}?timestamp=${obs.timestamp}`}>
                              <Mono>{titleForRun({runId: obs.runId})}</Mono>
                            </Link>
                            {` (${moment(Number(obs.timestamp)).from(
                              Number(timestamp),
                              true,
                            )} later)`}
                          </span>
                        </Box>
                        {entry.description}
                      </td>
                    </tr>
                  ))}
                </React.Fragment>
              ))}

              {hasLineage && (
                <tr>
                  <td>Parent Materializations</td>
                  <td>
                    <AssetLineageElements elements={assetLineage} timestamp={timestamp} />
                  </td>
                </tr>
              )}
            </tbody>
          </DetailsTable>
        ) : (
          <Box padding={{horizontal: 24, vertical: 12}}>No materialization event metadata</Box>
        )}
      </td>
    </tr>
  );
});

const EventGroupRow: React.FC<{
  group: AssetEventGroup;
  hasPartitions: boolean;
  hasLineage: boolean;
  isFocused: boolean;
}> = React.memo(({group, hasPartitions, hasLineage, isFocused}) => {
  const {latest, partition, timestamp, all} = group;

  const focusCss = isFocused
    ? {paddingLeft: 4, borderLeft: `4px solid ${Colors.HighlightGreen}`}
    : {paddingLeft: 8};

  const run = latest?.runOrError.__typename === 'Run' ? latest.runOrError : undefined;
  const repositoryOrigin = run?.repositoryOrigin;
  const repoAddress = repositoryOrigin
    ? buildRepoAddress(repositoryOrigin.repositoryName, repositoryOrigin.repositoryLocationName)
    : null;
  const repo = useRepository(repoAddress);

  if (!latest) {
    return (
      <>
        <td style={{whiteSpace: 'nowrap', paddingLeft: 24}}>{partition || <NoneSpan />}</td>
        <td colSpan={3} />
      </>
    );
  }

  if (!run) {
    return <span />;
  }

  return (
    <>
      {hasPartitions && (
        <td style={{whiteSpace: 'nowrap', ...focusCss}}>
          <Group direction="row" spacing={2}>
            <DisclosureTriangle open={isFocused} />
            {partition || <NoneSpan />}
          </Group>
        </td>
      )}
      <td style={hasPartitions ? {} : focusCss}>
        <Group direction="row" spacing={4}>
          {!hasPartitions && <DisclosureTriangle open={isFocused} />}
          <Group direction="column" spacing={4}>
            <Timestamp timestamp={{ms: Number(timestamp)}} />
            {all?.length > 1 ? (
              <AllIndividualEventsLink
                hasPartitions={hasPartitions}
                hasLineage={hasLineage}
                events={all}
              />
            ) : latest.__typename === 'MaterializationEvent' ? (
              <Box flex={{gap: 8, alignItems: 'center'}} style={{color: Colors.Gray600}}>
                <Icon name="materialization" size={16} color={Colors.Gray600} />
                Materialization
              </Box>
            ) : (
              <Box flex={{gap: 8, alignItems: 'center'}} style={{color: Colors.Gray600}}>
                <Icon name="observation" size={16} color={Colors.Gray600} /> Observation
              </Box>
            )}
          </Group>
        </Group>
      </td>
      <td>
        {!isHiddenAssetGroupJob(run.pipelineName) && (
          <Box margin={{bottom: 4}}>
            <Box padding={{left: 8}}>
              <PipelineReference
                showIcon
                pipelineName={run.pipelineName}
                pipelineHrefContext={repoAddress || 'repo-unknown'}
                snapshotId={run.pipelineSnapshotId}
                isJob={isThisThingAJob(repo, run.pipelineName)}
              />
            </Box>
            <Group direction="row" padding={{left: 8}} spacing={8} alignItems="center">
              <Icon name="linear_scale" color={Colors.Gray400} />
              <Link to={linkToRunEvent(run, latest)}>{latest.stepKey}</Link>
            </Group>
          </Box>
        )}
      </td>
      <td>
        <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
          <RunStatusWithStats runId={run.runId} status={run.status} />
          <Link to={`/instance/runs/${run.runId}?timestamp=${timestamp}`}>
            <Mono>{titleForRun(run)}</Mono>
          </Link>
        </Box>
      </td>
    </>
  );
});

const HoverableRow = styled.tr`
  &:hover {
    background: ${Colors.Gray10};
  }
`;

const DetailsTable = styled.table`
  width: 100%;
  margin: -2px -2px -3px;
  tr td {
    font-size: 14px;
  }
`;

interface PredecessorDialogProps {
  hasLineage: boolean;
  hasPartitions: boolean;
  events: (AssetMaterializationFragment | AssetObservationFragment)[];
}

export const AllIndividualEventsLink: React.FC<PredecessorDialogProps> = ({
  hasLineage,
  hasPartitions,
  events,
}) => {
  const [open, setOpen] = React.useState(false);
  const [focused, setFocused] = React.useState<AssetEventGroup | undefined>();
  const groups = React.useMemo(
    () =>
      events.map((p) => ({
        latest: p,
        partition: p.partition || undefined,
        timestamp: p.timestamp,
        all: [],
      })),
    [events],
  );
  const count = events.length;
  const title = () => {
    if (hasPartitions) {
      const partition = events[0].partition;
      if (partition) {
        return `Materialization and observation events for ${partition}`;
      }
    }
    return `Materialization and observation events`;
  };

  return (
    <>
      <ButtonLink onClick={() => setOpen(true)}>{`View ${count} events`}</ButtonLink>
      <Dialog
        isOpen={open}
        canEscapeKeyClose
        canOutsideClickClose
        onClose={() => setOpen(false)}
        style={{width: '80%', minWidth: '800px'}}
        title={title()}
      >
        {open && (
          <Box padding={{bottom: 8}} onClick={(e) => e.stopPropagation()}>
            <AssetEventsTable
              hasLineage={hasLineage}
              hasPartitions={hasPartitions}
              focused={focused}
              setFocused={setFocused}
              groups={groups}
            />
          </Box>
        )}
        <DialogFooter>
          <Button intent="primary" onClick={() => setOpen(false)}>
            OK
          </Button>
        </DialogFooter>
      </Dialog>
    </>
  );
};

const DisclosureTriangle: React.FC<{open: boolean; onClick?: () => void}> = ({open, onClick}) => (
  <DisclosureTriangleButton onClick={onClick} $open={open}>
    <Icon name="arrow_drop_down" size={24} />
  </DisclosureTriangleButton>
);

const DisclosureTriangleButton = styled.button<{$open: boolean}>`
  padding: 4px;
  margin: -4px;
  cursor: pointer;
  border: 0;
  background: transparent;
  outline: none;

  ${IconWrapper} {
    margin: -2px -5px;
    transform: ${({$open}) => ($open ? 'rotate(0deg)' : 'rotate(-90deg)')};
    opacity: 0.25;
  }

  :focus {
    outline: none;

    ${IconWrapper} {
      background: ${Colors.Dark};
      opacity: 0.5;
    }
  }
`;
