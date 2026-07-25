import { createMDX } from 'fumadocs-mdx/next';

const withMDX = createMDX();

/** @type {import('next').NextConfig} */
const config = {
  trailingSlash: true,
  reactStrictMode: true,
  output: 'export',
  images: {
    unoptimized: true,
  },
};

export default withMDX(config);
