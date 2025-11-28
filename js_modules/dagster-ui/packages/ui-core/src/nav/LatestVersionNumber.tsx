import {FontFamily} from '@dagster-io/ui-components';
import {useEffect, useState} from 'react';
import styled from 'styled-components';

export const LatestVersionNumber = () => {
  const {version} = useLatestVersionNumber();
  return (
    <LatestVersion>
      <span>{version || ' '}</span>
    </LatestVersion>
  );
};

const DAGSTER_PROJECT_ID = 'dagster-io/dagster';
const GITHUB_URL = 'https://api.github.com/repos/' + DAGSTER_PROJECT_ID + '/releases/latest';

export const useLatestVersionNumber = () => {
  const [version, setVersion] = useState<string | null>(() =>
    sessionStorage.getItem('dagster_latest_version'),
  );
  const [loading, setLoading] = useState(!version);

  useEffect(() => {
    if (version) {
      setLoading(false);
      return;
    }

    const fetchVersion = async () => {
      try {
        const response = await fetch(GITHUB_URL);
        const data = await response.json();
        const v = data.tag_name;
        setVersion(v);
        sessionStorage.setItem('dagster_latest_version', v);
      } catch (error) {
        console.error('Error fetching latest Dagster version:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchVersion();
  }, [version]);

  return {version, loading};
};

const LatestVersion = styled.div`
  font-size: 11px;
  font-family: ${FontFamily.monospace};
`;
