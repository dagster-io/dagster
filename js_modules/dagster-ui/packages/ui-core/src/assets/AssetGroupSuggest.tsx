import {Icon, MenuItem, Suggest} from '@dagster-io/ui-components';
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

export const AssetGroupSuggest: React.FC<{
  assets: Asset[];
  value: AssetGroupSelector | null;
  onChange: (g: AssetGroupSelector | null) => void;
}> = ({assets, value, onChange}) => {
  const assetGroups = React.useMemo(
    () =>
      uniqBy(
        (assets || []).map(buildAssetGroupSelector).filter((a) => !!a) as AssetGroupSelector[],
        (a) => JSON.stringify(a),
      ).sort((a, b) => a.groupName.localeCompare(b.groupName)),
    [assets],
  );

  const repoContextNeeded = React.useMemo(() => {
    // This is a bit tricky - the first time we find a groupName it sets the key to `false`.
    // The second time, it sets the value to `true` + tells use we need to show the repo name
    const result: {[groupName: string]: boolean} = {};
    assetGroups.forEach(
      (group) => (result[group.groupName] = result.hasOwnProperty(group.groupName)),
    );
    return result;
  }, [assetGroups]);

  return (
    <Suggest<AssetGroupSelector>
      selectedItem={value}
      items={assetGroups}
      inputProps={{
        style: {width: 220},
        placeholder: 'Filter asset groups…',
        rightElement: value ? (
          <ClearButton onClick={() => onChange(null)} style={{marginTop: 5, marginRight: 4}}>
            <Icon name="cancel" />
          </ClearButton>
        ) : undefined,
      }}
      inputValueRenderer={(partition) => partition.groupName}
      itemPredicate={(query, partition) =>
        query.length === 0 || partition.groupName.includes(query)
      }
      itemsEqual={isEqual}
      itemRenderer={(assetGroup, props) => (
        <MenuItem
          active={props.modifiers.active}
          onClick={props.handleClick}
          key={JSON.stringify(assetGroup)}
          text={
            <>
              {assetGroup.groupName}
              {repoContextNeeded[assetGroup.groupName] ? (
                <span style={{opacity: 0.5, paddingLeft: 4}}>
                  {buildRepoPathForHuman(
                    assetGroup.repositoryName,
                    assetGroup.repositoryLocationName,
                  )}
                </span>
              ) : undefined}
            </>
          }
        />
      )}
      noResults={<MenuItem disabled={true} text="No asset groups" />}
      onItemSelect={onChange}
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
