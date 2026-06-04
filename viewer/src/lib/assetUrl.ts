/** Resolve static assets for Vercel subpaths and local dev. */
export function assetUrl(path: string): string {
  const base = import.meta.env.BASE_URL || "/";
  const clean = path.replace(/^\//, "");
  return `${base.endsWith("/") ? base : `${base}/`}${clean}`;
}
