import {Box, Colors} from '@dagster-io/ui-components';

import {DAGSTER_TYPE_WITH_TOOLTIP_FRAGMENT, TypeWithTooltip} from './TypeWithTooltip';
import {gql} from '../apollo-client';
import {TypeListFragment} from './types/TypeList.types';
import {SidebarSection, SidebarSubhead, SidebarTitle} from '../pipelines/SidebarComponents';
import styles from './css/TypeList.module.css';

interface ITypeListProps {
  isGraph: boolean;
  types: Array<TypeListFragment>;
}

function groupTypes(types: TypeListFragment[]): {[key: string]: TypeListFragment[]} {
  const groups = {
    Custom: Array<TypeListFragment>(),
    'Built-in': Array<TypeListFragment>(),
  };
  types.forEach((type) => {
    if (type.isBuiltin) {
      groups['Built-in'].push(type);
    } else {
      groups['Custom'].push(type);
    }
  });
  return groups;
}

export const TypeList = (props: ITypeListProps) => {
  const groups = groupTypes(props.types);
  return (
    <>
      <SidebarSubhead />
      <Box padding={{vertical: 16, horizontal: 24}}>
        <SidebarTitle>{props.isGraph ? 'Graph types' : 'Pipeline types'}</SidebarTitle>
      </Box>
      {Object.entries(groups).map(([title, typesForSection], idx) => {
        const collapsedByDefault = idx !== 0 || typesForSection.length === 0;
        return (
          <SidebarSection key={idx} title={title} collapsedByDefault={collapsedByDefault}>
            <Box padding={{vertical: 16, horizontal: 24}}>
              {typesForSection.length ? (
                <ul className={styles.styledUL}>
                  {typesForSection.map((type, i) => (
                    <li className={styles.typeLI} key={i}>
                      <TypeWithTooltip type={type} />
                    </li>
                  ))}
                </ul>
              ) : (
                <div style={{color: Colors.textLight(), fontSize: '12px'}}>None</div>
              )}
            </Box>
          </SidebarSection>
        );
      })}
    </>
  );
};

export const TYPE_LIST_FRAGMENT = gql`
  fragment TypeListFragment on DagsterType {
    name
    isBuiltin
    ...DagsterTypeWithTooltipFragment
  }

  ${DAGSTER_TYPE_WITH_TOOLTIP_FRAGMENT}
`;
