import {IconName, MiddleTruncate, Tag, Tooltip, UnstyledButton} from '@dagster-io/ui-components';
import {ReactNode} from 'react';
import {Link} from 'react-router-dom';

import {buildTagMap} from './buildTagMap';
import styles from './css/RunTargetsCell.module.css';
import {getRepoAddress} from './getRepoAddress';
import {MappedRunsFeedEntry} from './mapRunsFeedData';
import {
  displayNameForAssetKey,
  isHiddenAssetGroupJob,
  tokenForAssetKey,
} from '../../asset-graph/Utils';
import {labelForAssetCheck} from '../../assets/AssetListUtils';
import {PipelineTag} from '../../pipelines/PipelineReference';
import {numberFormatter} from '../../ui/formatters';
import {RepoAddress} from '../../workspace/types';
import {DagsterTag} from '../RunTag';

type RunEntry = Extract<MappedRunsFeedEntry, {__typename: 'Run'}>;
type BackfillEntry = Extract<MappedRunsFeedEntry, {__typename: 'PartitionBackfill'}>;

type PreviewItem = {
  key: string;
  label: string;
};

const formatCount = (count: number, singular: string, plural: string) =>
  count === 1 ? `1 ${singular}` : `${numberFormatter.format(count)} ${plural}`;

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

type PartitionTagProps = {
  label: string;
};

const PartitionTag = ({label}: PartitionTagProps) => (
  <Tag icon="partition" className={styles.tag}>
    <div className={styles.partitionText}>
      <MiddleTruncate text={label} />
    </div>
  </Tag>
);

type TargetLinkProps = {
  href: string;
  onViewDetails?: () => void;
  tooltip?: ReactNode;
  // Names the link by its text alone, without the tag icon's name in front.
  label?: string;
  children: ReactNode;
};

// Opens the caller's targets dialog when there is one; otherwise the entry page holds the full list.
const TargetLink = ({href, onViewDetails, tooltip, label, children}: TargetLinkProps) => {
  const link =
    onViewDetails === undefined ? (
      <Link className={styles.tag} to={href} aria-label={label}>
        {children}
      </Link>
    ) : (
      <UnstyledButton className={styles.tag} onClick={onViewDetails} aria-label={label}>
        {children}
      </UnstyledButton>
    );

  if (tooltip === undefined) {
    return link;
  }

  return (
    <Tooltip content={tooltip} placement="top">
      {link}
    </Tooltip>
  );
};

type PreviewTooltipProps = {
  title: string;
  items: PreviewItem[];
  hiddenCount: number;
};

const PreviewTooltip = ({title, items, hiddenCount}: PreviewTooltipProps) => (
  <div className={styles.preview}>
    <div className={styles.previewTitle}>{title}</div>
    {items.map(({key, label}) => (
      <MiddleTruncate key={key} text={label} showTitle={false} />
    ))}
    {hiddenCount > 0 && <div>+{numberFormatter.format(hiddenCount)} more</div>}
  </div>
);

type CountTagProps = {
  icon: IconName;
  singular: string;
  plural: string;
  count: number;
  items: PreviewItem[];
  href: string;
  onViewDetails?: () => void;
};

const CountTag = ({icon, singular, plural, count, items, href, onViewDetails}: CountTagProps) => {
  const label = formatCount(count, singular, plural);
  return (
    <TargetLink
      href={href}
      onViewDetails={onViewDetails}
      label={label}
      tooltip={
        <PreviewTooltip
          title={`Selected ${plural}`}
          items={items}
          hiddenCount={count - items.length}
        />
      }
    >
      <Tag icon={icon} interactive>
        {label}
      </Tag>
    </TargetLink>
  );
};

type RunTargetsProps = {
  entry: RunEntry;
  onViewDetails?: () => void;
};

const RunTargets = ({entry, onViewDetails}: RunTargetsProps) => {
  const {assets, checks} = entry.selectionPreviews;
  const partitionLabel = getPartitionLabel(buildTagMap(entry.tags));
  const isSelectionUnknown = assets === null || checks === null;

  return (
    <>
      {!isHiddenAssetGroupJob(entry.jobName) && (
        <JobTag jobName={entry.jobName} repoAddress={getRepoAddress(entry)} />
      )}
      {partitionLabel !== null && <PartitionTag label={partitionLabel} />}
      {assets !== null && assets.count > 0 && (
        <CountTag
          icon="asset"
          singular="asset"
          plural="assets"
          count={assets.count}
          items={assets.preview.map((assetKey) => ({
            key: tokenForAssetKey(assetKey),
            label: displayNameForAssetKey(assetKey),
          }))}
          href={entry.href}
          onViewDetails={onViewDetails}
        />
      )}
      {checks !== null && checks.count > 0 && (
        <CountTag
          icon="asset_check"
          singular="check"
          plural="checks"
          count={checks.count}
          items={checks.preview.map((check) => ({
            key: JSON.stringify([tokenForAssetKey(check.assetKey), check.name]),
            label: labelForAssetCheck(check),
          }))}
          href={entry.href}
          onViewDetails={onViewDetails}
        />
      )}
      {isSelectionUnknown && (
        <TargetLink href={entry.href} onViewDetails={onViewDetails}>
          View targets
        </TargetLink>
      )}
    </>
  );
};

type BackfillIdentityProps = {
  entry: BackfillEntry;
};

// The feed carries no asset backfill targets yet, so only job and partition set backfills name one.
const BackfillIdentity = ({entry}: BackfillIdentityProps) => {
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
};

type RunTargetsCellProps = {
  entry: MappedRunsFeedEntry;
  onViewDetails?: () => void;
};

export const RunTargetsCell = ({entry, onViewDetails}: RunTargetsCellProps) => (
  <div className={styles.cell}>
    {entry.__typename === 'PartitionBackfill' ? (
      <BackfillIdentity entry={entry} />
    ) : (
      <RunTargets entry={entry} onViewDetails={onViewDetails} />
    )}
  </div>
);
