import type {NextConfig} from 'next';

const nextConfig: NextConfig = {
  transpilePackages: ['@dagster-io/dg-docs-components'],
  output: 'export',
};

export default nextConfig;
