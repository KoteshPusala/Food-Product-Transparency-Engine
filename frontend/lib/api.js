const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/* ================================================================
   ANALYZE BY BARCODE
   ================================================================ */
export async function analyzeByBarcode(barcode, includeAi = true) {
  try {
    const res = await fetch(
      `${BASE}/api/product/barcode/${barcode}?include_ai=${includeAi}`
    );

    if (!res.ok) {
      throw new Error(`Product not found (${res.status})`);
    }

    return await res.json();

  } catch (err) {
    console.error("Barcode error:", err);
    throw err;
  }
}

/* ================================================================
   SEARCH PRODUCTS (🔥 FIXED)
   ================================================================ */
export async function searchProducts(query) {
  try {
    // 🔹 Try your backend first
    const res = await fetch(
      `${BASE}/api/product/search?q=${encodeURIComponent(query)}&page_size=6`
    );

    if (res.ok) {
      const data = await res.json();
      const results = Array.isArray(data) ? data : data.products || [];

      if (results.length > 0) {
        return results; // ✅ backend worked
      }
    }

    // 🔥 FALLBACK → OpenFoodFacts (THIS FIXES YOUR ISSUE)
    const offRes = await fetch(
      `https://world.openfoodfacts.org/cgi/search.pl?search_terms=${encodeURIComponent(query)}&search_simple=1&action=process&json=1`
    );

    if (!offRes.ok) return [];

    const offData = await offRes.json();

    return (offData.products || []).slice(0, 6).map(p => ({
      name: p.product_name,
      brand: p.brands,
      image_url: p.image_front_url,
      barcode: p.code
    }));

  } catch (err) {
    console.error("Search error:", err);
    return [];
  }
}
/* ================================================================
   SEARCH + ANALYZE
   ================================================================ */
export async function searchAndAnalyze(query, includeAi = true) {
  try {
    const res = await fetch(
      `${BASE}/api/product/search/analyze?q=${encodeURIComponent(query)}&include_ai=${includeAi}`
    );

    if (!res.ok) {
      throw new Error(`Product not found (${res.status})`);
    }

    return await res.json();

  } catch (err) {
    console.error("Analyze error:", err);
    throw err;
  }
}

/* ================================================================
   COLORS
   ================================================================ */
export function gradeColor(grade) {
  const map = {
    'A+': '#00ff88',
    A: '#00dd66',
    B: '#88ff00',
    C: '#ffaa00',
    D: '#ff6600',
    F: '#ff3366'
  };
  return map[grade] || '#6b6b8a';
}

export function statusColor(status) {
  if (status === 'safe') return '#00ff88';
  if (status === 'caution') return '#ffaa00';
  if (status === 'harmful') return '#ff3366';
  return '#6b6b8a';
}

export function verdictColor(verdict) {
  if (!verdict) return '#6b6b8a';

  const v = verdict.toLowerCase();

  if (v.includes('safe')) return '#00ff88';
  if (v.includes('caution')) return '#ffaa00';
  if (v.includes('avoid')) return '#ff3366';

  return '#6b6b8a';
}