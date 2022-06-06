import {Suggest, MenuItem, Icon, Colors} from '@dagster-io/ui';
import isEqual from 'lodash/isEqual';
import uniqBy from 'lodash/uniqBy';
import * as React from 'react';

import {AssetGroupSelector} from '../types/globalTypes';
import {buildRepoPath} from '../workspace/buildRepoAddress';

interface AssetInGroup {
  definition: {
    groupName: string | null;
    repository: {name: string; location: {name: string}};
  } | null;
}

export const AssetGroupSuggest: React.FC<{
  assets: AssetInGroup[];
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
    const result: {[groupName: string]: boolean} = {};
    assetGroups.forEach(
      (group) => (result[group.groupName] = group.groupName in result ? true : false),
    );
    return result;
  }, [assetGroups]);

  return (
    <Suggest<AssetGroupSelector>
      selectedItem={value}
      items={assetGroups}
      resetOnClose
      inputProps={{
        style: {width: 220},
        placeholder: 'Filter asset groups…',
        rightElement: value ? (
          <div style={{marginTop: 6.5, marginRight: 6}} onClick={() => onChange(null)}>
            <Icon name="cancel" color={Colors.Gray400} />
          </div>
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
                  {buildRepoPath(assetGroup.repositoryName, assetGroup.repositoryLocationName)}
                </span>
              ) : undefined}
            </>
          }
        />
      )}
      noResults={<MenuItem disabled={true} text="No asset groups." />}
      onItemSelect={onChange}
    />
  );
};

export function buildAssetGroupSelector(a: AssetInGroup) {
  return a.definition && a.definition.groupName
    ? {
        groupName: a.definition.groupName,
        repositoryName: a.definition?.repository.name,
        repositoryLocationName: a.definition?.repository.location.name,
      }
    : false;
}
