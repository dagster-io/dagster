export type IntegrationConfig = {
  frontmatter: IntegrationFrontmatter;
  content: string;
};

export type IntegrationFrontmatter = {
  id: string;
  title: string;
  name: string;
  description: string;
  partnerlink: string;
  logoFilename: string | null;
  tags: string[];
  pypi: string;
  source: string;
};
