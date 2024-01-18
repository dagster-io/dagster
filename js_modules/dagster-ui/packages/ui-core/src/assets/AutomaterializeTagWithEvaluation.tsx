import * as React from 'react';
import {Link} from 'react-router-dom';

import {Box, Icon, MiddleTruncate, Popover, Tag} from '@dagster-io/ui-components';

import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {AssetKey} from './types';

const COLLATOR = new Intl.Collator(navigator.language, {sensitivity: 'base'});

interface Props {
  assetKeys: AssetKey[];
  evaluationId: string;
}

export const AutomaterializeTagWithEvaluation = ({assetKeys, evaluationId}: Props) => {
  const sortedKeys = React.useMemo(() => {
    return [...assetKeys].sort((a, b) => COLLATOR.compare(a.path.join('/'), b.path.join('/')));
  }, [assetKeys]);

  return (
    <Popover
      placement="bottom"
      content={
        <div style={{width: '340px'}}>
          <Box padding={{vertical: 8, horizontal: 12}} border="bottom" style={{fontWeight: 600}}>
            Auto-materialized
          </Box>
          <Box
            flex={{direction: 'column', gap: 12}}
            padding={{vertical: 12}}
            style={{maxHeight: '220px', overflowY: 'auto'}}
          >
            {sortedKeys.map((assetKey) => {
              const url = assetDetailsPathForKey(assetKey, {
                view: 'auto-materialize-history',
                evaluation: evaluationId,
              });
              return (
                <Box
                  key={url}
                  padding={{vertical: 8, left: 12, right: 16}}
                  flex={{
                    direction: 'row',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    gap: 8,
                  }}
                  style={{overflow: 'hidden'}}
                >
                  <Box
                    flex={{direction: 'row', alignItems: 'center', gap: 8}}
                    style={{overflow: 'hidden'}}
                  >
                    <Icon name="asset" />
                    <MiddleTruncate text={assetKey.path.join('/')} />
                  </Box>
                  <Link to={url} style={{whiteSpace: 'nowrap'}}>
                    View evaluation
                  </Link>
                </Box>
              );
            })}
          </Box>
        </div>
      }
      interactionKind="hover"
    >
      <Tag icon="auto_materialize_policy">Auto-materialized</Tag>
    </Popover>
  );
};
