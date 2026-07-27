/**
 * The prefix the site is served under, empty unless it is deployed to a project page.
 *
 * `basePath` in the Next config rewrites the URLs Next itself produces, which covers every link
 * and asset. It does not reach a path written by hand, so anything fetched at runtime has to be
 * prefixed with this.
 */
export const basePath = process.env.PAGES_BASE_PATH ?? '';
