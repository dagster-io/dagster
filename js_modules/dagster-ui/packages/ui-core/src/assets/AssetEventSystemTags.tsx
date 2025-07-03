import {Box, ButtonLink, Caption, Icon, Mono} from '@dagster-io/ui-components';

import styles from './css/AssetEventSystemTags.module.css';
import {AssetEventGroup} from './groupByPartition';
import {useStateWithStorage} from '../hooks/useStateWithStorage';
import {DagsterTag} from '../runs/RunTag';

// There can be other keys in the event tags, but we want to show data and code version
// at the top consistently regardless of their alphabetical / backend ordering.
const ORDER = [
  DagsterTag.AssetEventDataVersion.valueOf(),
  DagsterTag.AssetEventDataVersionDeprecated.valueOf(),
  DagsterTag.AssetEventCodeVersion.valueOf(),
];

export const AssetEventSystemTags = ({
  event,
  paddingLeft,
  collapsible,
}: {
  event: AssetEventGroup['latest'] | null;
  paddingLeft?: number;
  collapsible?: boolean;
}) => {
  const [shown, setShown] = useStateWithStorage('show-asset-system-tags', Boolean);

  if (collapsible && !shown) {
    return (
      <Caption>
        <ButtonLink onClick={() => setShown(true)}>
          <Box flex={{alignItems: 'center'}}>
            <span>Show tags ({event?.tags.length || 0})</span>
            <Icon name="arrow_drop_down" style={{transform: 'rotate(0deg)'}} />
          </Box>
        </ButtonLink>
      </Caption>
    );
  }

  return (
    <>
      <table className={styles.assetEventSystemTagsTable}>
        <tbody>
          {event?.tags.length ? (
            [...event.tags]
              .sort((a, b) => ORDER.indexOf(b.key) - ORDER.indexOf(a.key))
              .map((t) => (
                <tr key={t.key}>
                  <td style={{paddingLeft}}>
                    <Mono>{t.key.replace(DagsterTag.Namespace, '')}</Mono>
                  </td>
                  <td>{t.value}</td>
                </tr>
              ))
          ) : (
            <tr>
              <td style={{paddingLeft}}>No tags to display.</td>
            </tr>
          )}
        </tbody>
      </table>
      {collapsible && (
        <Caption>
          <ButtonLink onClick={() => setShown(false)}>
            <Box flex={{alignItems: 'center'}}>
              <span>Hide tags</span>
              <Icon name="arrow_drop_down" style={{transform: 'rotate(180deg)'}} />
            </Box>
          </ButtonLink>
        </Caption>
      )}
    </>
  );
};
