import {IntegrationTag} from './IntegrationTag';
import {KnownTagType} from '../graph/OpTags';

export type IntegrationConfig = {
  id: string;
  name: string;
  icon: KnownTagType;
  tags: IntegrationTag[];
};

export type IntegrationDetails = {
  id: string;
  status: 'published' | 'unpublished';
  name: string;
  title: string;
  excerpt: string;
  date: string;
  apireflink?: string;
  docslink?: string;
  partnerlink?: string;
  logo: KnownTagType;
  categories: string[];
  enabledBy: string[];
  enables?: string[];
  tags: IntegrationTag[];
  markdown: string;
};
