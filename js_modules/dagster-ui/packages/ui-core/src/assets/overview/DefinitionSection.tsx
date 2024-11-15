import {
  Box,
  ButtonLink,
  Caption,
  Colors,
  Icon,
  MiddleTruncate,
  Tag,
  Tooltip,
} from '@dagster-io/ui-components';
import dayjs from 'dayjs';
import React from 'react';
import {Link} from 'react-router-dom';
import {UserDisplay} from 'shared/runs/UserDisplay.oss';
import styled from 'styled-components';

import {AssetDefinedInMultipleReposNotice} from '../AssetDefinedInMultipleReposNotice';
import {AttributeAndValue} from './Common';
import {showSharedToaster} from '../../app/DomUtils';
import {useCopyToClipboard} from '../../app/browser';
import {CodeLink, getCodeReferenceKey} from '../../code-links/CodeLink';
import {AssetKind, isCanonicalStorageKindTag, isSystemTag} from '../../graph/KindTags';
import {useStateWithStorage} from '../../hooks/useStateWithStorage';
import {
  isCanonicalCodeSourceEntry,
  isCanonicalTableNameEntry,
  isCanonicalUriEntry,
} from '../../metadata/TableSchema';
import {RepositoryLink} from '../../nav/RepositoryLink';
import {buildTagString} from '../../ui/tagAsString';
import {WorkspaceLocationNodeFragment} from '../../workspace/WorkspaceContext/types/WorkspaceQueries.types';
import {RepoAddress} from '../../workspace/types';
import {workspacePathFromAddress} from '../../workspace/workspacePath';
import {AssetNodeDefinitionFragment} from '../types/AssetNodeDefinition.types';
import {AssetTableDefinitionFragment} from '../types/AssetTableFragment.types';

export const DefinitionSection = ({
  repoAddress,
  location,
  assetNode,
  cachedOrLiveAssetNode,
}: {
  repoAddress: RepoAddress | null;
  location: WorkspaceLocationNodeFragment | undefined;
  assetNode: AssetNodeDefinitionFragment | null | undefined;
  cachedOrLiveAssetNode: AssetNodeDefinitionFragment | AssetTableDefinitionFragment;
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
            to={workspacePathFromAddress(
              repoAddress!,
              `/asset-groups/${cachedOrLiveAssetNode.groupName}`,
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
            loadedFromRepo={repoAddress!}
          />
          <RepositoryLink repoAddress={repoAddress!} />
          {location && (
            <Caption color={Colors.textLighter()}>
              Loaded {dayjs.unix(location.updatedTimestamp).fromNow()}
            </Caption>
          )}
        </Box>
      </AttributeAndValue>
      <AttributeAndValue label="Owners">
        {cachedOrLiveAssetNode.owners &&
          cachedOrLiveAssetNode.owners.length > 0 &&
          cachedOrLiveAssetNode.owners.map((owner, idx) =>
            owner.__typename === 'UserAssetOwner' ? (
              <UserAssetOwnerWrapper key={idx}>
                <UserDisplay key={idx} email={owner.email} size="very-small" />
              </UserAssetOwnerWrapper>
            ) : (
              <Tag icon="people" key={idx}>
                {owner.team}
              </Tag>
            ),
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
                <CopyButton value={tableNameMetadata.text} />
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
                <CopyButton
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

const CopyButton = ({value}: {value: string}) => {
  const copy = useCopyToClipboard();
  const onCopy = async () => {
    copy(value);
    await showSharedToaster({
      intent: 'success',
      icon: 'copy_to_clipboard_done',
      message: 'Copied!',
    });
  };

  return (
    <Tooltip content="Copy" placement="bottom" display="block">
      <div onClick={onCopy} style={{cursor: 'pointer'}}>
        <Icon name="content_copy" />
      </div>
    </Tooltip>
  );
};

const UserAssetOwnerWrapper = styled.div`
  > div {
    background-color: ${Colors.backgroundGray()};
  }
`;
