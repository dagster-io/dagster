import {Colors} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';
import styles from './TypeWithTooltip.module.css';

import {gql} from '../apollo-client';

interface ITypeWithTooltipProps {
  type: {
    name: string | null;
    displayName: string;
    description: string | null;
  };
}

export const TypeWithTooltip = (props: ITypeWithTooltipProps) => {
  const {name, displayName} = props.type;

  // TODO: link to most inner type
  if (name) {
    return (
      <Link className={styles.typeLink} to={{search: `?tab=types&typeName=${displayName}`}}>
        <code className={styles.typeName}>{displayName}</code>
      </Link>
    );
  }

  return <code className={styles.typeName}>{displayName}</code>;
};

export const DAGSTER_TYPE_WITH_TOOLTIP_FRAGMENT = gql`
  fragment DagsterTypeWithTooltipFragment on DagsterType {
    name
    displayName
    description
  }
`;

