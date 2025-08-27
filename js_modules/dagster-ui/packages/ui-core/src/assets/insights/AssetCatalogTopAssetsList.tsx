import {
  BodySmall,
  Box,
  Button,
  HorizontalControls,
  Icon,
  ListItem,
  MiddleTruncate,
  MonoSmall,
  Tooltip,
} from '@dagster-io/ui-components';
import {useMemo, useState} from 'react';
import {Link} from 'react-router-dom';

import {formatMetric} from '../../insights/formatMetric';
import {ReportingUnitType} from '../../insights/types';
import {compactNumber, numberFormatter} from '../../ui/formatters';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {AssetActionMenu} from '../AssetActionMenu';
import {assetDetailsPathForKey} from '../assetDetailsPathForKey';
import {useAllAssets} from '../useAllAssets';
import styles from './css/AssetCatalogTopAssetsList.module.css';

const PAGE_SIZE = 10;

interface Props {
  values: {label: string; value: number}[];
  unitType: ReportingUnitType;
  unitLabel: string;
}

export const AssetCatalogTopAssetsList = ({values, unitType, unitLabel}: Props) => {
  const [page, setPage] = useState(0);
  const {assetsByAssetKey} = useAllAssets();

  const totalPages = Math.ceil(values.length / PAGE_SIZE);
  const currentPageValues = useMemo(
    () => values.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE),
    [page, values],
  );

  return (
    <>
      <div className={styles.list}>
        {currentPageValues.map(({label, value}, ii) => {
          const assetKey = label.split(' / ');
          const assetKeyString = assetKey.join('/');
          const maybeAsset = assetsByAssetKey.get(assetKeyString);
          const repoAddress = maybeAsset?.definition
            ? buildRepoAddress(
                maybeAsset.definition.repository.name,
                maybeAsset.definition.repository.location.name,
              )
            : null;
          const href = assetDetailsPathForKey({path: assetKey});
          const rowValue =
            unitType === ReportingUnitType.TIME_MS
              ? formatMetric(value, unitType)
              : compactNumber(value);
          const tooltipValue =
            unitType === ReportingUnitType.TIME_MS
              ? formatMetric(value, unitType)
              : numberFormatter.format(value);

          return (
            <ListItem
              key={label}
              index={ii}
              href={href}
              padding={{vertical: 8, horizontal: 4}}
              renderLink={({href, ...rest}) => <Link to={href ?? '#'} {...rest} />}
              left={
                <Box flex={{direction: 'row', gap: 4}}>
                  <div className={styles.rank}>{ii + 1}.</div>
                  <div className={styles.assetName}>
                    <MiddleTruncate text={label} />
                  </div>
                </Box>
              }
              right={
                <Box padding={{left: 16}}>
                  <HorizontalControls
                    controls={[
                      {
                        key: 'value',
                        control: (
                          <MonoSmall className={styles.valueContainer}>
                            <span className={styles.fullValue}>{tooltipValue}</span>
                            <Tooltip
                              className={styles.truncatedValue}
                              placement="top"
                              canShow={value > 1000}
                              content={
                                <span className={styles.tooltipContent}>
                                  {unitLabel}:{' '}
                                  <span className={styles.tooltipValue}>{tooltipValue}</span>
                                </span>
                              }
                            >
                              <div className={styles.truncatedValue}>{rowValue}</div>
                            </Tooltip>
                          </MonoSmall>
                        ),
                      },
                      {
                        key: 'action-menu',
                        control: (
                          <AssetActionMenu
                            unstyledButton
                            path={assetKey}
                            definition={maybeAsset?.definition || null}
                            repoAddress={repoAddress}
                          />
                        ),
                      },
                    ]}
                  />
                </Box>
              }
            />
          );
        })}
      </div>
      {totalPages > 1 && (
        <Box
          flex={{
            alignItems: 'flex-end',
            grow: 1,
            direction: 'row',
          }}
        >
          <Box
            flex={{
              direction: 'row',
              grow: 1,
              alignItems: 'flex-end',
              justifyContent: 'stretch',
            }}
            border="top"
            padding={{top: 12, horizontal: 8}}
          >
            <Box
              flex={{
                direction: 'row',
                gap: 12,
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
              style={{width: '100%'}}
            >
              <BodySmall>
                {page + 1} of {totalPages}
              </BodySmall>
              <Box flex={{direction: 'row', gap: 4}}>
                <Button
                  outlined
                  onClick={() => setPage(page - 1)}
                  disabled={page === 0}
                  icon={<Icon name="arrow_back" />}
                />
                <Button
                  outlined
                  onClick={() => setPage(page + 1)}
                  disabled={page === totalPages - 1}
                  icon={<Icon name="arrow_forward" />}
                />
              </Box>
            </Box>
          </Box>
        </Box>
      )}
    </>
  );
};
