import {Box, ButtonLink, Icon, MiddleTruncate, Popover, Tag} from '@dagster-io/ui-components';
import {useMemo, useState} from 'react';

import {EvaluationDetailDialog} from './AutoMaterializePolicyPage/EvaluationDetailDialog';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {AssetKey} from './types';

const COLLATOR = new Intl.Collator(navigator.language, {sensitivity: 'base'});

type OpenEvaluation = {
  assetKeyPath: string[];
  evaluationId: string;
};

interface Props {
  assetKeys: AssetKey[];
  evaluationId: string;
}

export const AutomaterializeTagWithEvaluation = ({assetKeys, evaluationId}: Props) => {
  const [openEvaluation, setOpenEvaluation] = useState<OpenEvaluation | null>(null);

  const sortedKeys = useMemo(() => {
    return [...assetKeys].sort((a, b) => COLLATOR.compare(a.path.join('/'), b.path.join('/')));
  }, [assetKeys]);

  return (
    <>
      <Popover
        placement="bottom"
        content={
          <div style={{width: '400px'}}>
            <Box padding={{vertical: 8, horizontal: 12}} border="bottom" style={{fontWeight: 600}}>
              Automation condition
            </Box>
            <Box
              flex={{direction: 'column', gap: 16}}
              padding={{vertical: 12}}
              style={{maxHeight: '220px', overflowY: 'auto'}}
            >
              {sortedKeys.map((assetKey) => {
                const url = assetDetailsPathForKey(assetKey, {
                  view: 'automation',
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
                      gap: 16,
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
                    <ButtonLink
                      onClick={() => setOpenEvaluation({assetKeyPath: assetKey.path, evaluationId})}
                      style={{whiteSpace: 'nowrap'}}
                    >
                      View evaluation
                    </ButtonLink>
                  </Box>
                );
              })}
            </Box>
          </div>
        }
        interactionKind="hover"
      >
        <Tag icon="automation_condition">Automation condition</Tag>
      </Popover>
      <EvaluationDetailDialog
        assetKeyPath={openEvaluation?.assetKeyPath ?? []}
        isOpen={!!openEvaluation}
        onClose={() => setOpenEvaluation(null)}
        evaluationID={openEvaluation?.evaluationId ?? ''}
      />
    </>
  );
};
