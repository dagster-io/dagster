export type IntegrationConfig = {
  frontmatter: IntegrationFrontmatter;
  content: string;
};

export type IntegrationFrontmatter = {
  id: string;
  status: string;
  name: string;
  title: string;
  excerpt: string;
  logoFilename: string | null;
  pypiUrl: string | null;
  repoUrl: string | null;
  partnerlink: string;
  categories: string[];
  enabledBy: string[];
  enables: string[];
  tags: string[];
};
