import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import sitemap from '@astrojs/sitemap';

// https://astro.build/config
export default defineConfig({
  site: 'https://amsumo9.github.io',
  base: '/medical-negligence-lawyers-directory',
  integrations: [tailwind(), sitemap()],
  output: 'static',
  build: {
    format: 'directory'
  }
});
