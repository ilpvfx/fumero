import { docs } from '@/.source/server';
import { loader } from 'fumadocs-core/source';
import { icons } from 'lucide-react';
import { createElement } from 'react';
import { fumeroPlugin } from '@/components/mdx/pdx-plugin';

export const source = loader({
  plugins: [fumeroPlugin()],
  icon(icon) {
    if (!icon) {
      return;
    }

    if (icon in icons) return createElement(icons[icon as keyof typeof icons]);
  },
  baseUrl: '/',
  source: docs.toFumadocsSource(),
});
