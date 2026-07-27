import type { BaseLayoutProps } from "fumadocs-ui/layouts/shared";
import Image from 'next/image';
import { version } from '@/lib/version';

/**
 * Shared layout configurations
 *
 * you can customise layouts individually from:
 * Home Layout: app/(home)/layout.tsx
 * Docs Layout: app/docs/layout.tsx
 */
export const baseOptions: BaseLayoutProps = {
  nav: {
    title: (
      <>
        <Image
          src="/ilp-logo-black.svg"
          alt="ilp"
          width="24"
          height="24"
          className="mr-2 dark:hidden"
        />
        <Image
          src="/ilp-logo.svg"
          alt="ilp"
          width="24"
          height="24"
          className="mr-2 hidden dark:inline"
        />
        Fumero
        <span className="ml-2 rounded-md border border-fd-border bg-fd-muted/50 px-1.5 py-0.5 font-mono text-[10px] leading-normal text-fd-muted-foreground">
          {`v${version}`}
        </span>
      </>
    ),
  },
  links: [],
  githubUrl: "https://github.com/ilpvfx/fumero"
};
