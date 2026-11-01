import {IconName, MiddleTruncate, Tag, Tooltip} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';

import styles from './css/RunTargets.module.css';
import {MappedRunsFeedEntry} from './mapRunsFeedData';
import {displayNameForAssetKey, tokenForAssetKey} from '../../asset-graph/Utils';
import {labelForAssetCheck} from '../../assets/AssetListUtils';
import {numberFormatter} from '../../ui/formatters';

type PreviewItem = {
  key: string;
  label: string;
};

const formatCount = (count: number, singular: string, plural: string) =>
  count === 1 ? `1 ${singular}` : `${numberFormatter.format(count)} ${plural}`;

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
};

const CountTag = ({icon, singular, plural, count, items, href}: CountTagProps) => {
  const label = formatCount(count, singular, plural);
  return (
    <Tooltip
      content={
        <PreviewTooltip
          title={`Selected ${plural}`}
          items={items}
          hiddenCount={count - items.length}
        />
      }
      placement="top"
    >
      <Link className={styles.tag} to={href} aria-label={label}>
        <Tag icon={icon} interactive>
          {label}
        </Tag>
      </Link>
    </Tooltip>
  );
};

type RunTargetsProps = {
  entry: MappedRunsFeedEntry;
};

export const RunTargets = ({entry}: RunTargetsProps) => {
  // The feed carries no backfill targets yet, so backfills show none.
  if (entry.__typename !== 'Run') {
    return null;
  }

  const {assets, checks} = entry.selectionPreviews;

  return (
    <>
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
        />
      )}
    </>
  );
};
