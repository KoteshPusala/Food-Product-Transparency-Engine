'use client'
import { useState } from 'react'
import { statusColor } from '../lib/api'

export default function IngredientCard({ analysis }) {
  const [expanded, setExpanded] = useState(false)
  const { name, status, explanation, pubchem_data, papers } = analysis
  const statusSafe = status?.toLowerCase() || "unknown"
  const color = statusColor(statusSafe)
  
  // Get status display text
  const getStatusText = () => {
    switch(statusSafe) {
      case 'safe': return 'SAFE';
      case 'moderate': return 'MODERATE';
      case 'harmful': return 'HARMFUL';
      default: return 'UNKNOWN';
    }
  }
  
  // Get status icon
 const statusIcon = { 
    safe: '✓', 
    moderate: '⚠', 
    harmful: '✕',
    unknown: 'ℹ'
  }[statusSafe] || 'ℹ'
  // Dynamic classes based on status
  const getStatusBadgeClass = () => {
    switch(statusSafe) {
      case 'safe': return 'status-badge-safe'
      case 'moderate': return 'status-badge-moderate'
      case 'harmful': return 'status-badge-harmful'
      default: return 'status-badge-unknown'
    }
  }
  
  const getIconCircleClass = () => {
    switch(statusSafe) {
      case 'safe': return 'icon-circle-safe'
      case 'moderate': return 'icon-circle-moderate'
      case 'harmful': return 'icon-circle-harmful'
      default: return 'icon-circle-unknown'
    }
  }
  
  return (
    <div
      className={`ingredient-card ${expanded ? 'expanded' : ''}`}
      onClick={() => setExpanded(!expanded)}
    >
      <div className="ingredient-card-inner">
        {/* Status icon circle */}
        <div className={`icon-circle ${getIconCircleClass()}`}>
          {statusIcon}
        </div>

        <div className="ingredient-card-content">
          <div className="ingredient-card-header">
            <h4 className="ingredient-name">{name}</h4>
            <span className={`status-badge ${getStatusBadgeClass()}`}>
              {getStatusText()}
            </span>
          </div>
          <p className="ingredient-explanation line-clamp-2">{explanation}</p>
        </div>

        <span className="expand-icon">{expanded ? '▲' : '▼'}</span>
      </div>

      {/* Expanded section */}
      {expanded && (
        <div className="ingredient-expanded">
          {/* PubChem data */}
          {pubchem_data && pubchem_data.cid && (
            <div className="pubchem-section">
              <p className="section-label">🔬 PUBCHEM DATA</p>
              <div className="pubchem-content">
                {pubchem_data.molecular_formula && (
                  <p className="pubchem-formula">
                    <span className="text-gray-500">Formula: </span>
                    <span className="formula-value">{pubchem_data.molecular_formula}</span>
                  </p>
                )}
                {pubchem_data.safety_summary && (
                  <p className="pubchem-summary">{pubchem_data.safety_summary}</p>
                )}
                {pubchem_data.hazard_statements?.length > 0 && (
                  <div className="hazard-tags">
                    {pubchem_data.hazard_statements.slice(0, 3).map((h, i) => (
                      <span key={i} className="hazard-tag">{h.split(':')[0]}</span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Research papers */}
          {papers?.length > 0 && (
            <div className="papers-section">
              <p className="section-label">📄 RESEARCH PAPERS</p>
              <div className="papers-list">
                {papers.map((paper, i) => (
                  <a
                    key={i}
                    href={paper.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={e => e.stopPropagation()}
                    className="paper-card"
                  >
                    <p className="paper-title line-clamp-2">{paper.title}</p>
                    <div className="paper-meta">
                      <span className="paper-year">{paper.year}</span>
                      {paper.is_open_access && (
                        <span className="open-access-badge">Open Access</span>
                      )}
                    </div>
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}