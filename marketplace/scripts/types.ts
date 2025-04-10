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
  partnerlink: string;
  logoFilename: string | null;
  categories: string[];
  enabledBy: string[];
  enables: string[];
  tags: string[];
};
