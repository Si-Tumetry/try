/**
 * Build-time switches. Set in infra/render.yaml, or in a local .env file, as VITE_* variables.
 * Member pages are hidden from navigation until the REST API is deployed (docs/DEPLOYMENT.md).
 */
export const MEMBER_PAGES_ENABLED = import.meta.env.VITE_MEMBER_PAGES === 'true';
