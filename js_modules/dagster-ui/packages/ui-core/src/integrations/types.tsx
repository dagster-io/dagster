export type IntegrationConfig = {
  frontmatter: IntegrationFrontmatter;
  content: string;
  logo: string | StaticImageData | null;
};

export type IntegrationFrontmatter = {
  id: string;
  status: string;
  name: string;
  title: string;
  excerpt: string;
  partnerlink: string;
  categories: string[];
  enabledBy: string[];
  enables: string[];
  tags: string[];
};
