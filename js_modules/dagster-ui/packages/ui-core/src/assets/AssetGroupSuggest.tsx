import {Box, Checkbox, Icon, MenuItem, Suggest} from '@dagster-io/ui-components';
import isEqual from 'lodash/isEqual';
import uniqBy from 'lodash/uniqBy';
import * as React from 'react';

import {AssetGroupSelector} from '../graphql/types';
import {ClearButton} from '../ui/ClearButton';
import {buildRepoPathForHuman} from '../workspace/buildRepoAddress';

type Asset = {
  definition: {
    groupName: string | null;
    repository: {name: string; location: {name: string}};
  } | null;
};

export function useAssetGroupSelectorsForAssets(assets: Asset[] | undefined) {
  return React.useMemo(
    () =>
      uniqBy(
        (assets || []).map(buildAssetGroupSelector).filter((a) => !!a) as AssetGroupSelector[],
        (a) => JSON.stringify(a),
      ).sort((a, b) => a.groupName.localeCompare(b.groupName)),
    [assets],
  );
}

// We're using a <Suggest /> component because it's convenient to have typeahead behavior,
// but we want to support mulit-selection. To achieve this, we show checkboxes on the items
// and override the label text ("2 groups"). Blueprint doesn't need to know what the real
// selection is, just that one exists.
const FAKE_SELECTED_ITEM: AssetGroupSelector = {
  groupName: '-',
  repositoryLocationName: '-',
  repositoryName: '-',
};

export const AssetGroupSuggest: React.FC<{
  assetGroups: AssetGroupSelector[];
  value: AssetGroupSelector[];
  onChange: (g: AssetGroupSelector[]) => void;
}> = ({assetGroups, value, onChange}) => {
  const repoKey = (g: AssetGroupSelector) => `${g.repositoryName}@${g.repositoryLocationName}`;
  const repoKey1 = assetGroups[0] ? repoKey(assetGroups[0]) : '';
  const repoContextNeeded = !assetGroups.every((g) => repoKey1 === repoKey(g));

  return (
    <Suggest<AssetGroupSelector>
      selectedItem={value.length ? FAKE_SELECTED_ITEM : null}
      items={assetGroups}
      menuWidth={300}
      inputProps={{
        style: {width: 200},
        placeholder: 'Filter asset groups…',
        rightElement: value.length ? (
          <ClearButton onClick={() => onChange([])} style={{marginTop: 5, marginRight: 4}}>
            <Icon name="cancel" />
          </ClearButton>
        ) : undefined,
      }}
      inputValueRenderer={() =>
        value.length === 1 ? value[0]!.groupName : value.length > 1 ? `${value.length} groups` : ``
      }
      itemPredicate={(query, partition) =>
        query.length === 0 || partition.groupName.toLowerCase().includes(query.toLowerCase())
      }
      itemsEqual={isEqual}
      itemRenderer={(assetGroup, props) => (
        <MenuItem
          active={props.modifiers.active}
          onClick={props.handleClick}
          key={JSON.stringify(assetGroup)}
          text={
            <Box
              flex={{direction: 'row', gap: 6, alignItems: 'center'}}
              margin={{left: 4}}
              style={{maxWidth: '500px'}}
            >
              <Checkbox checked={value.some((g) => isEqual(g, assetGroup))} size="small" readOnly />
              <Box
                flex={{direction: 'row', alignItems: 'center', grow: 1, shrink: 1}}
                style={{overflow: 'hidden'}}
              >
                <div style={{overflow: 'hidden'}}>
                  {assetGroup.groupName}
                  {repoContextNeeded ? (
                    <span style={{opacity: 0.5, paddingLeft: 4}}>
                      {buildRepoPathForHuman(
                        assetGroup.repositoryName,
                        assetGroup.repositoryLocationName,
                      )}
                    </span>
                  ) : undefined}
                </div>
              </Box>
            </Box>
          }
        />
      )}
      noResults={<MenuItem disabled={true} text="No asset groups" />}
      closeOnSelect={false}
      resetOnQuery={false}
      onItemSelect={(item) => {
        const nextValue = value.filter((g) => !isEqual(item, g));
        if (nextValue.length === value.length) {
          nextValue.push(item);
        }
        onChange(nextValue);
      }}
    />
  );
};

export function buildAssetGroupSelector(a: Asset) {
  return a.definition && a.definition.groupName
    ? {
        groupName: a.definition.groupName,
        repositoryName: a.definition.repository.name,
        repositoryLocationName: a.definition.repository.location.name,
      }
    : null;
}
