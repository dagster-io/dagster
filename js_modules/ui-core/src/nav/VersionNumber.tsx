import {gql, useQuery} from '../apollo-client';
import styles from './css/VersionNumber.module.css';
import {VersionNumberQuery, VersionNumberQueryVariables} from './types/VersionNumber.types';

export const VersionNumber = () => {
  const {version} = useVersionNumber();
  return (
    <div className={styles.version}>
      <span>{version || ' '}</span>
    </div>
  );
};

export const useVersionNumber = () => {
  const {data, loading} = useQuery<VersionNumberQuery, VersionNumberQueryVariables>(
    VERSION_NUMBER_QUERY,
  );
  return {version: data?.version, loading: !data && loading};
};

export const VERSION_NUMBER_QUERY = gql`
  query VersionNumberQuery {
    version
  }
`;
