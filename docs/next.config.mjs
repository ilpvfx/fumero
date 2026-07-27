import { createMDX } from 'fumadocs-mdx/next';

const withMDX = createMDX();

// A project site on GitHub Pages is served from /<repository>/ rather than from the domain root,
// so the export has to be told its prefix. The release workflow passes the one Pages reports.
// Left unset, as it is locally and on a custom domain, the site stays at the root.
const basePath = process.env.PAGES_BASE_PATH || undefined;

/** @type {import('next').NextConfig} */
const config = {
  basePath,
  trailingSlash: true,
  reactStrictMode: true,
  output: 'export',
  images: {
    unoptimized: true,
  },
};

export default withMDX(config);
