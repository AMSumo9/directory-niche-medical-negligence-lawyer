import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import sitemap from '@astrojs/sitemap';

// Use DEPLOY_TARGET to determine if we're deploying to GitHub Pages
// For local development, run: npm run dev
// For GitHub Pages deployment, run: DEPLOY_TARGET=github npm run build
const isGitHubPages = process.env.DEPLOY_TARGET === 'github';

// https://astro.build/config
export default defineConfig({
  site: isGitHubPages
    ? 'https://amsumo9.github.io'
    : 'http://localhost:4321',
  base: isGitHubPages
    ? '/directory-niche-medical-negligence-lawyer'
    : '/',
  integrations: [tailwind(), sitemap()],
  output: 'static',
  build: {
    format: 'directory'
  }
});
