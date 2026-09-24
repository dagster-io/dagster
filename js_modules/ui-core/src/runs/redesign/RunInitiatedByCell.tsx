import {ButtonLink, Colors, Icon, IconName, MiddleTruncate, Tag} from '@dagster-io/ui-components';
import {UserDisplay} from '@shared/runs/UserDisplay';
import {Link} from 'react-router-dom';

import styles from './css/RunInitiatedByCell.module.css';
import {Initiator, TickIdentifier, getInitiatedBy} from './getInitiatedBy';
import {MappedRunsFeedEntry} from './mapRunsFeedData';
import {shortenId} from '../../util/shortenId';
import {getBackfillPath} from '../RunsFeedUtils';

type InitiatorDisplay = {
  icon: IconName;
  label: string;
  href: string | null;
};

const getInitiatorDisplay = (initiator: Initiator): InitiatorDisplay => {
  switch (initiator.kind) {
    case 'reexecution':
      return {
        icon: 'cached',
        label: initiator.isAutomatic ? 'Auto retry of' : 'Re-execution of',
        href: null,
      };
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
        label: initiator.label,
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

type ParentRunTagProps = {
  runId: string;
};

const ParentRunTag = ({runId}: ParentRunTagProps) => (
  <Tag className={styles.tag}>
    <Link to={`/runs/${runId}`} className={styles.idLink}>
      {shortenId(runId)}
    </Link>
  </Tag>
);

type BackfillTagProps = {
  backfillId: string;
};

const BackfillTag = ({backfillId}: BackfillTagProps) => (
  <Tag icon="backfill" className={styles.tag}>
    <Link to={getBackfillPath(backfillId)} className={styles.idLink}>
      {backfillId}
    </Link>
  </Tag>
);

type TickDetailsTagProps = {
  tick: TickIdentifier;
  onOpenTickDetails: (tick: TickIdentifier, triggerElement: HTMLElement) => void;
};

const TickDetailsTag = ({tick, onOpenTickDetails}: TickDetailsTagProps) => (
  <Tag icon="checklist" className={styles.tag}>
    <ButtonLink onClick={(event) => onOpenTickDetails(tick, event.currentTarget)}>
      View tick
    </ButtonLink>
  </Tag>
);

type RunInitiatedByCellProps = {
  entry: MappedRunsFeedEntry;
  onOpenTickDetails: (tick: TickIdentifier, triggerElement: HTMLElement) => void;
};

export const RunInitiatedByCell = ({entry, onOpenTickDetails}: RunInitiatedByCellProps) => {
  const {initiator, user, parentBackfillId, tick} = getInitiatedBy(entry);
  const {icon, label, href} = getInitiatorDisplay(initiator);

  return (
    <div className={styles.cell}>
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
      {initiator.kind === 'reexecution' && <ParentRunTag runId={initiator.parentRunId} />}
      {parentBackfillId && <BackfillTag backfillId={parentBackfillId} />}
      {user && (
        <span className={styles.tag}>
          <UserDisplay email={user} />
        </span>
      )}
      {tick && <TickDetailsTag tick={tick} onOpenTickDetails={onOpenTickDetails} />}
    </div>
  );
};
