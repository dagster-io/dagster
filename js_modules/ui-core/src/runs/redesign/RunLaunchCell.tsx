import {ButtonLink, Colors, Icon, IconName, MiddleTruncate, Tag} from '@dagster-io/ui-components';
import {UserDisplay} from '@shared/runs/UserDisplay';
import {Link} from 'react-router-dom';

import {RunTargets} from './RunTargets';
import {buildTagMap} from './buildTagMap';
import styles from './css/RunLaunchCell.module.css';
import {Initiator, TickIdentifier, getLaunchDetails} from './getLaunchDetails';
import {getRepoAddress} from './getRepoAddress';
import {MappedRunsFeedEntry} from './mapRunsFeedData';
import {isHiddenAssetGroupJob} from '../../asset-graph/Utils';
import {PipelineTag} from '../../pipelines/PipelineReference';
import {shortenId} from '../../util/shortenId';
import {RepoAddress} from '../../workspace/types';
import {DagsterTag} from '../RunTag';
import {getBackfillPath} from '../RunsFeedUtils';

type InitiatorDisplay = {
  icon: IconName;
  label: string;
  href: string | null;
};

const getInitiatorDisplay = (initiator: Initiator): InitiatorDisplay => {
  switch (initiator.kind) {
    case 'schedule':
      return {
        icon: 'schedule',
        label: initiator.name,
        href: initiator.href,
      };
    case 'sensor':
      return {
        icon: 'sensors',
        label: initiator.name,
        href: initiator.href,
      };
    case 'declarative-automation':
      return {
        icon: 'automation_condition',
        label: initiator.name ?? 'Declarative automation',
        href: initiator.href,
      };
    case 'auto-observation':
      return {
        icon: 'auto_observe',
        label: 'Auto-observation',
        href: null,
      };
    case 'backfill':
      return {
        icon: 'backfill',
        label: 'Backfill',
        href: null,
      };
    case 'manual':
      return {
        icon: 'account_circle',
        label: 'Manual',
        href: null,
      };
  }
};

const getPartitionLabel = (tags: Map<string, string>) => {
  const partition = tags.get(DagsterTag.Partition);
  if (partition !== undefined) {
    return partition;
  }

  const start = tags.get(DagsterTag.AssetPartitionRangeStart);
  const end = tags.get(DagsterTag.AssetPartitionRangeEnd);
  if (start !== undefined && end !== undefined) {
    return `${start} → ${end}`;
  }

  return null;
};

type InitiatorLabelProps = {
  initiator: Initiator;
};

const InitiatorLabel = ({initiator}: InitiatorLabelProps) => {
  const {icon, label, href} = getInitiatorDisplay(initiator);
  return (
    <div className={styles.initiator}>
      <Icon name={icon} color={Colors.accentBlue()} className={styles.icon} />
      <div className={styles.label}>
        {href ? (
          <Link to={href}>
            <MiddleTruncate text={label} />
          </Link>
        ) : (
          <MiddleTruncate text={label} />
        )}
      </div>
    </div>
  );
};

type JobTagProps = {
  jobName: string;
  repoAddress: RepoAddress | null;
};

const JobTag = ({jobName, repoAddress}: JobTagProps) => (
  <span className={styles.tag}>
    <PipelineTag
      isJob
      showIcon
      pipelineName={jobName}
      pipelineHrefContext={repoAddress ?? 'repo-unknown'}
    />
  </span>
);

type JobAndPartitionTagsProps = {
  entry: MappedRunsFeedEntry;
};

const JobAndPartitionTags = ({entry}: JobAndPartitionTagsProps) => {
  if (entry.__typename === 'PartitionBackfill') {
    // Asset backfills have no job or partition set.
    if (entry.isAssetBackfill) {
      return null;
    }
    if (entry.backfillJobName !== null) {
      return <JobTag jobName={entry.backfillJobName} repoAddress={null} />;
    }
    if (entry.partitionSetName !== null) {
      return (
        <Tag icon="partition_set" className={styles.tag}>
          {entry.partitionSetName}
        </Tag>
      );
    }
    return null;
  }

  const partitionLabel = getPartitionLabel(buildTagMap(entry.tags));
  return (
    <>
      {!isHiddenAssetGroupJob(entry.jobName) && (
        <JobTag jobName={entry.jobName} repoAddress={getRepoAddress(entry)} />
      )}
      {partitionLabel !== null && (
        <Tag icon="partition" className={styles.tag}>
          <div className={styles.partitionText}>
            <MiddleTruncate text={partitionLabel} />
          </div>
        </Tag>
      )}
    </>
  );
};

type ReexecutionTagProps = {
  entry: MappedRunsFeedEntry;
};

const ReexecutionTag = ({entry}: ReexecutionTagProps) => {
  if (entry.__typename !== 'Run' || entry.parentRunId === null) {
    return null;
  }

  const label = entry.isAutomaticRetry ? 'Retry of' : 'Re-execution of';
  return (
    <Tag icon="replay" className={styles.tag}>
      {label}{' '}
      <Link to={`/runs/${entry.parentRunId}`} className={styles.idLink}>
        {shortenId(entry.parentRunId)}
      </Link>
    </Tag>
  );
};

type RunLaunchCellProps = {
  entry: MappedRunsFeedEntry;
  onOpenTickDetails: (tick: TickIdentifier, triggerElement: HTMLElement) => void;
};

export const RunLaunchCell = ({entry, onOpenTickDetails}: RunLaunchCellProps) => {
  const {initiator, user, parentBackfillId, tick} = getLaunchDetails(entry);

  return (
    <div className={styles.cell}>
      <InitiatorLabel initiator={initiator} />
      {tick && (
        <Tag icon="checklist" className={styles.tag}>
          <ButtonLink onClick={(event) => onOpenTickDetails(tick, event.currentTarget)}>
            View tick
          </ButtonLink>
        </Tag>
      )}
      {parentBackfillId && (
        <Tag icon="backfill" className={styles.tag}>
          <Link to={getBackfillPath(parentBackfillId)} className={styles.idLink}>
            {parentBackfillId}
          </Link>
        </Tag>
      )}
      {user && (
        <span className={styles.tag}>
          <UserDisplay email={user} />
        </span>
      )}
      <JobAndPartitionTags entry={entry} />
      <RunTargets entry={entry} />
      <ReexecutionTag entry={entry} />
    </div>
  );
};
