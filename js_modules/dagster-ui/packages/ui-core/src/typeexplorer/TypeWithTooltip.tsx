import {Link} from 'react-router-dom';

import {gql} from '../apollo-client';
import styles from './css/TypeWithTooltip.module.css';

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
