import {useEffect, useMemo, useState} from 'react';

import {IntegrationConfig, IntegrationFrontmatter} from './types';

const INTEGRATIONS_HOSTNAME = 'https://integration-registry.dagster.io';
const INTEGRATIONS_LIST_URL = `${INTEGRATIONS_HOSTNAME}/api/integrations/index.json`;

export type IntegrationsProvider = {
  integrations: IntegrationFrontmatter[];
  fetchIntegrationDetails: (id: string) => Promise<IntegrationConfig | null>;

  canManageIntegrations?: boolean;
  addPrivateIntegrationDetails?: (integration: IntegrationConfig) => Promise<void>;
  updatePrivateIntegrationDetails?: (integration: IntegrationConfig) => Promise<void>;
  deletePrivateIntegrationDetails?: (integration: IntegrationConfig) => Promise<void>;
};

export const useIntegrationsProvider = (): IntegrationsProvider => {
  const [integrations, setIntegrations] = useState<IntegrationFrontmatter[]>([]);

  useEffect(() => {
    const fetchIntegrations = async () => {
      const res = await fetch(INTEGRATIONS_LIST_URL);
      let data: IntegrationFrontmatter[] = await res.json();

      // Filter out articles and sub-pages that do not have integration names
      data = data.filter((d) => !!d.name);

      setIntegrations(data);
    };
    fetchIntegrations();
  }, []);

  return useMemo(
    () => ({
      integrations,
      fetchIntegrationDetails: async (id: string) => {
        const url = `${INTEGRATIONS_HOSTNAME}/api/integrations/${id}.json`;
        const res = await fetch(url);
        return await res.json();
      },
    }),
    [integrations],
  );
};
