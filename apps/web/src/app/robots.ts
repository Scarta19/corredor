import type { MetadataRoute } from "next";

const base = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export default function robots(): MetadataRoute.Robots {
  // Staging and preview deployments must never be indexed: duplicate content
  // competing with the real site is worse than no content at all.
  const indexable = process.env.NEXT_PUBLIC_INDEXABLE === "true";

  return {
    rules: indexable
      ? { userAgent: "*", allow: "/" }
      : { userAgent: "*", disallow: "/" },
    sitemap: `${base}/sitemap.xml`,
  };
}
