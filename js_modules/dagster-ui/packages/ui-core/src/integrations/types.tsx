export type IntegrationConfig = {
  frontmatter: IntegrationFrontmatter;
  content: string;
};

export type IntegrationFrontmatter = {
  id: string;
  name: string;
  title: string;
  description: string;
  logoFilename: string | null;
  pypi: string | null;
  partnerlink: string;
  source: string;
  tags: string[];
};
