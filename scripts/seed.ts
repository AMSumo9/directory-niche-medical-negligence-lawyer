import { createClient } from '@supabase/supabase-js';
import * as dotenv from 'dotenv';

dotenv.config();

const supabase = createClient(
  process.env.PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

const states = [
  { name: 'Queensland', code: 'QLD', cities: ['Brisbane', 'Gold Coast', 'Cairns', 'Townsville', 'Sunshine Coast'] },
  { name: 'New South Wales', code: 'NSW', cities: ['Sydney', 'Newcastle', 'Wollongong', 'Central Coast'] },
  { name: 'Victoria', code: 'VIC', cities: ['Melbourne', 'Geelong', 'Ballarat'] },
  { name: 'South Australia', code: 'SA', cities: ['Adelaide', 'Mount Gambier'] },
  { name: 'Western Australia', code: 'WA', cities: ['Perth', 'Fremantle'] },
  { name: 'Tasmania', code: 'TAS', cities: ['Hobart', 'Launceston'] },
  { name: 'Australian Capital Territory', code: 'ACT', cities: ['Canberra'] },
  { name: 'Northern Territory', code: 'NT', cities: ['Darwin', 'Alice Springs'] }
];

async function seed() {
  console.log('🌱 Starting seed process...');

  const lawyers = [];
  let count = 0;

  for (const state of states) {
    for (const city of state.cities) {
      // Create 5 lawyers per city
      for (let i = 0; i < 5; i++) {
        count++;
        const firmName = `${city} Medical Law ${i + 1}`;
        const slug = firmName.toLowerCase().replace(/\s+/g, '-');

        // Determine subscription tier and featured status
        const isFeatured = count % 10 === 0;
        const isPremium = count % 5 === 0 && !isFeatured;
        const tier = isFeatured ? 'featured' : isPremium ? 'premium' : 'free';

        lawyers.push({
          firm_name: firmName,
          slug: slug,
          state: state.name,
          state_code: state.code,
          city: city,
          address: `${count} Legal Street, ${city}, ${state.code} ${3000 + count}`,
          phone: `(0${Math.floor(Math.random() * 8) + 2}) ${Math.floor(1000 + Math.random() * 9000)} ${Math.floor(1000 + Math.random() * 9000)}`,
          email: `contact@${slug}.com.au`,
          website: `https://${slug}.com.au`,
          show_phone_link: count % 3 === 0,
          show_email_link: count % 3 === 0,
          show_website_link: count % 3 === 0,
          description: `${firmName} specializes in medical negligence cases across ${city} and surrounding areas. Our experienced team has been helping victims of medical malpractice for over 20 years. We handle cases involving surgical errors, misdiagnosis, birth injuries, medication errors, and hospital negligence. Contact us today for a free consultation.`,
          short_description: `Expert medical negligence lawyers in ${city}, ${state.name}. Free consultation available.`,
          subscription_tier: tier,
          is_featured: isFeatured,
          featured_priority: isFeatured ? 100 - count : 0,
          is_published: true
        });
      }
    }
  }

  console.log(`📝 Inserting ${lawyers.length} lawyers...`);

  const { data, error } = await supabase
    .from('lawyers')
    .insert(lawyers)
    .select();

  if (error) {
    console.error('❌ Error inserting lawyers:', error);
    return;
  }

  console.log(`✅ Successfully inserted ${data.length} lawyers`);

  // Display some stats
  const featured = data.filter(l => l.is_featured).length;
  const premium = data.filter(l => l.subscription_tier === 'premium').length;
  const free = data.filter(l => l.subscription_tier === 'free').length;

  console.log('\n📊 Statistics:');
  console.log(`   Featured: ${featured}`);
  console.log(`   Premium: ${premium}`);
  console.log(`   Free: ${free}`);
  console.log(`   Total: ${data.length}`);
  console.log('\n✨ Seed complete!');
}

seed().catch(console.error);
