/**
 * THIS FILE IS GENERATED BY `yarn generate-integration-docs`.
 *
 * DO NOT EDIT MANUALLY.
 */

import {IntegrationFrontmatter} from '../types';
import cubeLogo from './logos/cube.svg';

export const logo = cubeLogo;

export const frontmatter: IntegrationFrontmatter = {
  id: 'cube',
  status: 'published',
  name: 'Cube',
  title: 'Dagster & Cube',
  excerpt: 'Push changes from upstream data sources to Cubes semantic layer.',
  partnerlink: 'https://cube.dev/',
  categories: ['Other'],
  enabledBy: [],
  enables: [],
  tags: ['community-supported'],
};

export const content =
  'With the `dagster_cube` integration you can setup Cube and Dagster to work together so that Dagster can push changes from upstream data sources to Cube using its integration API.\n\n### Installation\n\n```bash\npip install dagster_cube\n```\n\n### Example\n\n<CodeExample path="docs_snippets/docs_snippets/integrations/cube.py" language="python" />\n\n### About Cube\n\n**Cube.js** is the semantic layer for building data applications. It helps data engineers and application developers access data from modern data stores, organize it into consistent definitions, and deliver it to every application.';
