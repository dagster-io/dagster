export type IntegrationConfig = {
  frontmatter: IntegrationFrontmatter;
  content: string;
};

export type IntegrationFrontmatter = {
  id: string;
  name: string;
  title: string;
  description: string;
  logo: string | null;
  logoFilename: string | null;
  installationCommand: string | null;
  pypi: string | null;
  partnerlink: string;
  source: string;
  tags: string[];
  isPrivate: boolean;
};
