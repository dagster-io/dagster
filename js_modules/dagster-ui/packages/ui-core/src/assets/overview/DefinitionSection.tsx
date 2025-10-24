import {
  Box,
  ButtonLink,
  Caption,
  Colors,
  Icon,
  MiddleTruncate,
  Tag,
} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';

import {TimeFromNow} from '../../ui/TimeFromNow';
import {AssetDefinedInMultipleReposNotice} from '../AssetDefinedInMultipleReposNotice';
import {AttributeAndValue} from './Common';
import {CodeLink, getCodeReferenceKey} from '../../code-links/CodeLink';
import {AssetKind, isCanonicalStorageKindTag, isSystemTag} from '../../graph/KindTags';
import {useStateWithStorage} from '../../hooks/useStateWithStorage';
import {
  isCanonicalCodeSourceEntry,
  isCanonicalTableNameEntry,
  isCanonicalUriEntry,
} from '../../metadata/TableSchema';
import {RepositoryLink} from '../../nav/RepositoryLink';
import {DefinitionOwners} from '../../owners/DefinitionOwners';
import {CopyIconButton} from '../../ui/CopyButton';
import {buildTagString} from '../../ui/tagAsString';
import {WorkspaceLocationNodeFragment} from '../../workspace/WorkspaceContext/types/WorkspaceQueries.types';
import {RepoAddress} from '../../workspace/types';
import {globalAssetGraphPathForGroup} from '../globalAssetGraphPathToString';
import {AssetTableDefinitionFragment} from '../types/AssetTableFragment.types';
import {AssetViewDefinitionNodeFragment} from '../types/AssetView.types';

export const DefinitionSection = ({
  repoAddress,
  location,
  assetNode,
  cachedOrLiveAssetNode,
}: {
  repoAddress: RepoAddress | null;
  location: WorkspaceLocationNodeFragment | undefined;
  assetNode: AssetViewDefinitionNodeFragment | null | undefined;
  cachedOrLiveAssetNode: AssetViewDefinitionNodeFragment | AssetTableDefinitionFragment;
}) => {
  const storageKindTag = cachedOrLiveAssetNode.tags?.find(isCanonicalStorageKindTag);
  const filteredTags = cachedOrLiveAssetNode.tags?.filter(
    (tag) => tag.key !== 'dagster/storage_kind',
  );

  const nonSystemTags = filteredTags?.filter((tag) => !isSystemTag(tag));
  const systemTags = filteredTags?.filter(isSystemTag);

  const tableNameMetadata = assetNode?.metadataEntries?.find(isCanonicalTableNameEntry);
  const uriMetadata = assetNode?.metadataEntries?.find(isCanonicalUriEntry);
  const codeSource = assetNode?.metadataEntries?.find(isCanonicalCodeSourceEntry);

  return (
    <Box flex={{direction: 'column', gap: 12}}>
      <AttributeAndValue label="Group">
        <Tag icon="asset_group">
          <Link
            to={globalAssetGraphPathForGroup(
              cachedOrLiveAssetNode.groupName,
              cachedOrLiveAssetNode.assetKey,
            )}
          >
            {cachedOrLiveAssetNode.groupName}
          </Link>
        </Tag>
      </AttributeAndValue>

      <AttributeAndValue label="Code location">
        <Box flex={{direction: 'column'}}>
          <AssetDefinedInMultipleReposNotice
            assetKey={cachedOrLiveAssetNode.assetKey}
            // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
            loadedFromRepo={repoAddress!}
          />
          {/* eslint-disable-next-line @typescript-eslint/no-non-null-assertion */}
          <RepositoryLink repoAddress={repoAddress!} />
          {location && (
            <Caption color={Colors.textLighter()}>
              Loaded <TimeFromNow unixTimestamp={location.updatedTimestamp} />
            </Caption>
          )}
        </Box>
      </AttributeAndValue>
      <AttributeAndValue label="Owners">
        {cachedOrLiveAssetNode.owners && cachedOrLiveAssetNode.owners.length > 0 && (
          <DefinitionOwners owners={cachedOrLiveAssetNode.owners} />
        )}
      </AttributeAndValue>
      <AttributeAndValue label="Compute kind">
        {cachedOrLiveAssetNode.computeKind && (
          <AssetKind
            style={{position: 'relative'}}
            kind={cachedOrLiveAssetNode.computeKind}
            reduceColor
            linkToFilteredAssetsTable
          />
        )}
      </AttributeAndValue>
      <AttributeAndValue label="Kinds">
        {(cachedOrLiveAssetNode.kinds.length > 1 || !cachedOrLiveAssetNode.computeKind) &&
          cachedOrLiveAssetNode.kinds.map((kind) => (
            <AssetKind
              key={kind}
              style={{position: 'relative'}}
              kind={kind}
              reduceColor
              linkToFilteredAssetsTable
            />
          ))}
      </AttributeAndValue>
      <AttributeAndValue label="Storage">
        {(tableNameMetadata || uriMetadata || storageKindTag) && (
          <Box flex={{direction: 'column', gap: 4}} style={{minWidth: 0}}>
            {tableNameMetadata && (
              <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
                <MiddleTruncate text={tableNameMetadata.text} />
                <CopyIconButton value={tableNameMetadata.text} />
              </Box>
            )}
            {uriMetadata && (
              <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
                {uriMetadata.__typename === 'TextMetadataEntry' ? (
                  uriMetadata.text
                ) : (
                  <a target="_blank" rel="noreferrer" href={uriMetadata.url}>
                    {uriMetadata.url}
                  </a>
                )}
                <CopyIconButton
                  value={
                    uriMetadata.__typename === 'TextMetadataEntry'
                      ? uriMetadata?.text
                      : uriMetadata.url
                  }
                />
              </Box>
            )}
            {storageKindTag && (
              <AssetKind
                style={{position: 'relative'}}
                kind={storageKindTag.value}
                reduceColor
                linkToFilteredAssetsTable
              />
            )}
          </Box>
        )}
      </AttributeAndValue>
      <AttributeAndValue label="Tags">
        {filteredTags && filteredTags.length > 0 && (
          <Box flex={{direction: 'column', gap: 8}}>
            <Box>
              {nonSystemTags.map((tag, idx) => (
                <Tag key={idx}>{buildTagString(tag)}</Tag>
              ))}
            </Box>
            {systemTags.length > 0 && <SystemTagsToggle tags={systemTags} />}
          </Box>
        )}
      </AttributeAndValue>
      <AttributeAndValue label="Source code">
        {codeSource &&
          codeSource.codeReferences &&
          codeSource.codeReferences.map((ref) => (
            <CodeLink key={getCodeReferenceKey(ref)} sourceLocation={ref} />
          ))}
      </AttributeAndValue>
    </Box>
  );
};

const SystemTagsToggle = ({tags}: {tags: Array<{key: string; value: string}>}) => {
  const [shown, setShown] = useStateWithStorage('show-asset-definition-system-tags', Boolean);

  if (!shown) {
    return (
      <Caption>
        <ButtonLink onClick={() => setShown(true)}>
          <Box flex={{alignItems: 'center'}}>
            <span>Show system tags ({tags.length || 0})</span>
            <Icon name="arrow_drop_down" style={{transform: 'rotate(0deg)'}} />
          </Box>
        </ButtonLink>
      </Caption>
    );
  } else {
    return (
      <Box flex={{direction: 'column', gap: 8}}>
        <Box>
          {tags.map((tag, idx) => (
            <Tag key={idx}>{buildTagString(tag)}</Tag>
          ))}
        </Box>
        <Caption>
          <ButtonLink onClick={() => setShown(false)}>
            <Box flex={{alignItems: 'center'}}>
              <span>Hide system tags</span>
              <Icon name="arrow_drop_down" style={{transform: 'rotate(180deg)'}} />
            </Box>
          </ButtonLink>
        </Caption>
      </Box>
    );
  }
};
