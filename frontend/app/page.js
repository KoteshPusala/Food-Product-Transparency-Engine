'use client'
import { useState, useCallback } from 'react'
import { analyzeByBarcode, searchProducts, searchAndAnalyze, gradeColor, verdictColor } from '../lib/api'
import HealthScoreGauge from '../components/HealthScoreGauge'
import IngredientCard from '../components/IngredientCard'
import ProductCard from '../components/ProductCard'
import dynamic from 'next/dynamic'

const BarcodeScanner = dynamic(() => import('../components/BarcodeScanner'), { ssr: false })

export default function Home() {
  const [query, setQuery] = useState('')
  const [barcode, setBarcode] = useState('')
  const [mode, setMode] = useState('search')
  const [loading, setLoading] = useState(false)
  const [searchResults, setSearchResults] = useState([])
  const [analysis, setAnalysis] = useState(null)
  const [error, setError] = useState(null)
  const [showScanner, setShowScanner] = useState(false)
  const [includeAi, setIncludeAi] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')

  const reset = () => {
    setAnalysis(null)
    setSearchResults([])
    setError(null)
    setActiveTab('overview')
  }
  const normalize = (str) => {
    return str
      .toLowerCase()
      .replace(/[^a-z0-9\s]/g, '')   // remove special chars
      .replace(/\s+/g, ' ')          // remove extra spaces
      .trim()
  }
  const handleSearch = async (e) => {
    e?.preventDefault()
    if (!query.trim()) return

    reset()
    setLoading(true)

    try {
      const cleaned = normalize(query)

      const variations = [
        query,
        cleaned,
        cleaned.replace(/\s/g, ''),
        cleaned.split(' ')[0],
      ]

      let results = []

      for (let q of variations) {
        const res = await searchProducts(q)

        if (res && res.length > 0) {
          results = res
          break
        }
      }

      // 🔥 FINAL fallback
      if (results.length === 0) {
        const fallback = await searchProducts(cleaned.split(' ')[0])
        if (fallback && fallback.length > 0) {
          results = fallback
        }
      }

      // 🔥 EXTRA FILTER (VERY IMPORTANT)
      if (results.length > 0) {
        const filtered = results.filter(p =>
          (p.product_name || p.name || "")
            .toLowerCase()
            .includes(cleaned)
        )

        // if filtered found, use it, else keep original
        results = filtered.length > 0 ? filtered : results
      }

      if (results.length === 0) {
        setError("No results found. Try simpler name like 'Coca Cola'")
      } else {
        setSearchResults(results)
      }

    } catch (err) {
      setError("Search failed. Try again.")
    } finally {
      setLoading(false)
    }
  }
  const handleAnalyzeProduct = async (product) => {
    setSearchResults([])
    setLoading(true)
    setError(null)
    try {
      let data
      if (product.barcode) {
        data = await analyzeByBarcode(product.barcode, includeAi)
      } else {
        data = await searchAndAnalyze(product.name, includeAi)
      }
      setAnalysis(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleBarcodeSubmit = async (e) => {
    e?.preventDefault()
    if (!barcode.trim()) return
    reset()
    setLoading(true)
    try {
      const data = await analyzeByBarcode(barcode.trim(), includeAi)
      setAnalysis(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleScanDetected = useCallback(async (code) => {
    setShowScanner(false)
    setBarcode(code)
    reset()
    setLoading(true)
    try {
      const data = await analyzeByBarcode(code, includeAi)
      setAnalysis(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [includeAi])

  const verdict = analysis?.ai_analysis?.overall_verdict
  const vColor = verdictColor(verdict)

  return (
    <main className="main-container">
      {/* Hero Header */}
      <div className="hero-header">
        <div className="container">
          <div className="hero-content">
            <div className="hero-badge">
              <span className="hero-icon">🔬</span>
            </div>
            <span className="hero-label">Product Transparency Engine</span>
          </div>
          <h1 className="hero-title">
            Know What You<br />
            <span className="hero-highlight">Actually Eat</span>
          </h1>
          <p className="hero-description">
            AI-powered ingredient analysis. Search any product or scan its barcode to see real health risks, scientific research, and safer alternatives.
          </p>
        </div>
      </div>

      <div className="container main-content">
        {/* Mode Toggle + AI Toggle */}
        <div className="toggle-container">
          <div className="mode-toggle">
            {['search', 'barcode'].map(m => (
              <button
                key={m}
                onClick={() => { setMode(m); reset() }}
                className={`mode-btn ${mode === m ? 'mode-btn-active' : ''}`}
              >
                {m === 'search' ? '🔍 Search' : '📷 Barcode'}
              </button>
            ))}
          </div>

          <label className="ai-toggle">
            <span className="ai-toggle-label">AI Analysis</span>
            <div
              className={`ai-toggle-switch ${includeAi ? 'ai-toggle-active' : ''}`}
              onClick={() => setIncludeAi(!includeAi)}
            >
              <div className={`ai-toggle-knob ${includeAi ? 'ai-toggle-knob-active' : ''}`} />
            </div>
          </label>
        </div>

        {/* Search Input */}
        {mode === 'search' && (
          <form onSubmit={handleSearch} className="search-form">
            <input
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Search product name e.g. Nutella, Coca Cola..."
              className="search-input"
            />
            <button
              type="submit"
              disabled={loading}
              className="search-btn"
            >
              {loading ? '...' : 'Search'}
            </button>
          </form>
        )}

        {/* Barcode Input */}
        {mode === 'barcode' && (
          <div className="barcode-container">
            <form onSubmit={handleBarcodeSubmit} className="search-form">
              <input
                value={barcode}
                onChange={e => setBarcode(e.target.value)}
                placeholder="Enter barcode number e.g. 3017620422003"
                className="barcode-input"
              />
              <button
                type="submit"
                disabled={loading}
                className="search-btn"
              >
                {loading ? '...' : 'Analyze'}
              </button>
            </form>
            <button
              onClick={() => setShowScanner(true)}
              className="camera-btn-full"
            >
              📷 Open Camera Scanner
            </button>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="loading-container">
            <div className="spinner-wrapper">
              <div className="spinner-ring" />
              <div className="spinner-inner" />
            </div>
            <p className="loading-text">Analyzing ingredients...</p>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="error-card">
            
            <div className="error-icon">📦</div>

            <div className="error-content">
              <p className="error-title">Product not found</p>
              <p className="error-subtext">
                This Product is not available in the database. Try another product.
              </p>
            </div>

          </div>
        )}

        {/* Search Results */}
        {!loading && searchResults.length > 0 && (
          <div className="results-container">
            <p className="results-count">{searchResults.length} PRODUCTS FOUND — Click to analyze</p>
            {searchResults.map((p, i) => (
              <div key={i} className={`result-item fade-up-${Math.min(i+1,5)}`}>
                <ProductCard product={p} onClick={handleAnalyzeProduct} />
              </div>
            ))}
          </div>
        )}

        {/* Analysis Results */}
        {!loading && analysis && (
          <div className="analysis-container">
            {/* Product Header */}
            <div className="product-header-card">
              {analysis.product.image_url && (
                <img
                  src={analysis.product.image_url}
                  alt={analysis.product.name}
                  className="product-image"
                  onError={e => e.target.style.display='none'}
                />
              )}
              <div className="product-info">
                <h2 className="product-name">{analysis.product.name}</h2>
                {analysis.product.brand && <p className="product-brand">{analysis.product.brand}</p>}
                <div className="product-badges">
                  {analysis.product.nutriscore && (
                    <span className="badge-nutriscore">Nutriscore {analysis.product.nutriscore}</span>
                  )}
                  {analysis.product.nova_group && (
                    <span className="badge-nova">NOVA {analysis.product.nova_group}</span>
                  )}
                  {analysis.product.allergens?.slice(0,3).map((a, i) => (
                    <span key={i} className="badge-allergen">{a}</span>
                  ))}
                </div>
              </div>
              <button onClick={reset} className="close-btn">✕</button>
            </div>

            {/* AI Verdict Banner */}
            {analysis.ai_analysis?.overall_verdict && (
              <div className={`verdict-banner verdict-${verdict?.toLowerCase()}`}>
                <div className="verdict-header">
                  <span className="verdict-label">AI VERDICT</span>
                  <span className={`verdict-value verdict-${verdict?.toLowerCase()}`}>
                    {analysis.ai_analysis.overall_verdict}
                  </span>
                </div>
                <p className="verdict-summary">{analysis.ai_analysis.overall_summary}</p>
              </div>
            )}

            {/* Tabs */}
            <div className="tabs-container">
              {['overview', 'ingredients', 'research', 'advice'].map(tab => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`tab-btn ${activeTab === tab ? 'tab-active' : ''}`}
                >
                  {tab}
                </button>
              ))}
            </div>

            {/* Tab: Overview */}
            {activeTab === 'overview' && (
              <div className="overview-grid">
                <div className="score-card">
                  <p className="score-card-label">HEALTH SCORE</p>
                  <HealthScoreGauge score={analysis.score} />
                </div>

                <div className="nutrients-card">
                  <p className="nutrients-label">NUTRIENTS (per 100g)</p>
                  <div className="nutrients-list">
                    {Object.entries(analysis.product.nutrients).map(([key, n]) => {
                      const levelClass = n.level === 'high' ? 'level-high' : n.level === 'low' ? 'level-low' : 'level-medium'
                      const label = key.replace('_100g', '').replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
                      return (
                        <div key={key} className="nutrient-item">
                          <span className="nutrient-name">{label}</span>
                          <div className="nutrient-values">
                            <span className="nutrient-value">{n.value}{n.unit}</span>
                            <span className={`nutrient-level ${levelClass}`}>{n.level}</span>
                          </div>
                        </div>
                      )
                    })}
                    {Object.keys(analysis.product.nutrients).length === 0 && (
                      <p className="nutrient-empty">Nutrient data not available</p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Tab: Ingredients */}
            {activeTab === 'ingredients' && (
              <div className="ingredients-container">
                {analysis.ai_analysis?.ingredient_analyses?.length > 0 ? (
                  <>
                    <p className="ingredients-count">{analysis.ai_analysis.ingredient_analyses.length} INGREDIENTS ANALYZED</p>
                    {analysis.ai_analysis?.ingredient_analyses
                      ?.sort((a, b) => {
                        const order = { harmful: 0, moderate: 1, safe: 2 }
                        return (order[a.status] ?? 3) - (order[b.status] ?? 3)
                      })
                      .map((ing, idx) => (
                        <IngredientCard key={idx} analysis={ing} />
                    ))}
                  </>
                ) : (
                  <div className="empty-state">
                    <p className="empty-text">Enable AI Analysis to see ingredient-by-ingredient breakdown</p>
                  </div>
                )}

                {analysis.product.ingredients_text && (
                  <div className="full-ingredients">
                    <p className="full-ingredients-label">FULL INGREDIENTS LIST</p>
                    <p className="full-ingredients-text">{analysis.product.ingredients_text}</p>
                  </div>
                )}
              </div>
            )}

            {/* Tab: Research */}
            {activeTab === 'research' && (
              <div className="research-container">
                {analysis.top_papers?.length > 0 ? (
                  <>
                    <p className="research-count">{analysis.top_papers.length} RESEARCH PAPERS FOUND</p>
                    {analysis.top_papers.map((paper, i) => (
                      <a
                        key={i}
                        href={paper.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={`research-card fade-up-${Math.min(i+1,5)}`}
                      >
                        <div className="research-card-header">
                          <div className="research-card-content">
                            <p className="research-title">{paper.title}</p>
                            <div className="research-meta">
                              {paper.authors?.length > 0 && (
                                <span className="research-authors">{paper.authors.join(', ')}</span>
                              )}
                              {paper.year && <span className="research-year">· {paper.year}</span>}
                              {paper.journal && <span className="research-journal">· {paper.journal}</span>}
                            </div>
                            <div className="research-tags">
                              <span className="research-tag">{paper.ingredient_query}</span>
                              {paper.is_open_access && (
                                <span className="research-open">Open Access</span>
                              )}
                            </div>
                          </div>
                          <span className="research-arrow">↗</span>
                        </div>
                        {paper.abstract && (
                          <p className="research-abstract">{paper.abstract}</p>
                        )}
                      </a>
                    ))}
                  </>
                ) : (
                  <div className="empty-state">
                    <p className="empty-text">No research papers found for this product's harmful ingredients</p>
                  </div>
                )}
              </div>
            )}

            {/* Tab: Advice */}
            {activeTab === 'advice' && (
              <div className="advice-container">
                {analysis.ai_analysis?.recommendations?.length > 0 ? (
                  <div className="recommendations-card">
                    <p className="recommendations-label">RECOMMENDATIONS</p>
                    <div className="recommendations-list">
                      {analysis.ai_analysis.recommendations.map((rec, i) => (
                        <div key={i} className="recommendation-item">
                          <span className="recommendation-arrow">→</span>
                          <p className="recommendation-text">{rec}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null}

                {analysis.ai_analysis?.safer_alternatives && (
                  <div className="alternatives-card">
                    <p className="alternatives-label">SAFER ALTERNATIVES</p>
                    <p className="alternatives-text">{analysis.ai_analysis.safer_alternatives}</p>
                  </div>
                )}

                {!analysis.ai_analysis && (
                  <div className="empty-state">
                    <p className="empty-text">Enable AI Analysis to get personalized recommendations</p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Empty state */}
        {!loading && !analysis && searchResults.length === 0 && !error && (
          <div className="empty-state-large">
            <div className="empty-icon">🔬</div>
            <p className="empty-title">Ready to analyze</p>
            <p className="empty-description">
              Search a product name or enter a barcode to get a full health analysis powered by real scientific data
            </p>
            <div className="popular-products">
              {['Nutella', 'Coca Cola', 'Doritos', 'Oreo'].map(ex => (
                <button
                  key={ex}
                  onClick={() => { setQuery(ex); setMode('search') }}
                  className="popular-btn"
                >
                  {ex}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="footer">
        <p className="footer-text">
          Data from OpenFoodFacts · PubChem · PubMed · Groq AI · For informational purposes only
        </p>
      </div>

      {/* Scanner Modal */}
      {showScanner && (
        <BarcodeScanner
          onDetected={handleScanDetected}
          onClose={() => setShowScanner(false)}
        />
      )}
    </main>
  )
}


