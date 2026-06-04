'use client'

export default function ProductCard({ product, onClick }) {
  const { name, brand, image_url, nutriscore, nova_group, barcode } = product

  const getNutriscoreClass = (score) => {
    const classes = {
      'A': 'nutriscore-a',
      'B': 'nutriscore-b', 
      'C': 'nutriscore-c',
      'D': 'nutriscore-d',
      'E': 'nutriscore-e'
    }
    return classes[score] || 'nutriscore-default'
  }

  return (
    <div className="product-card" onClick={() => onClick(product)}>
      <div className="product-card-image">
        {image_url ? (
          <img src={image_url} alt={name} className="product-card-img" />
        ) : (
          <span className="product-card-emoji">🥫</span>
        )}
      </div>
      <div className="product-card-info">
        <h3 className="product-card-title">{name || 'Unknown Product'}</h3>
        {brand && <p className="product-card-brand">{brand}</p>}
        <div className="product-card-badges">
          {nutriscore && (
            <span className={`product-badge ${getNutriscoreClass(nutriscore)}`}>
              {nutriscore}
            </span>
          )}
          {nova_group && (
            <span className="product-badge nova-badge">
              NOVA {nova_group}
            </span>
          )}
        </div>
      </div>
      <span className="product-card-arrow">→</span>
    </div>
  )
}