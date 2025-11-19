import {FontFamily} from '@dagster-io/ui-components';
import {useEffect, useState} from 'react';
import styled from 'styled-components';

export const VersionNumber = () => {
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
  const [version, setVersion] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchVersion = async () => {
      try {
        const response = await fetch(GITHUB_URL);
        const data = await response.json();
        setVersion(data.tag_name);
      } catch (error) {
        console.error('Error fetching latest Dagster version:', error);
        setVersion(null);
      } finally {
        setLoading(false);
      }
    };

    fetchVersion();
  }, []);

  return {version, loading};
};

const LatestVersion = styled.div`
  font-size: 11px;
  font-family: ${FontFamily.monospace};
`;
