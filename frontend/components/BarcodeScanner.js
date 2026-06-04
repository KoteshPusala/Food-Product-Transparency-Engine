'use client'
import { useEffect, useRef, useState } from 'react'
import { Html5QrcodeScanner } from 'html5-qrcode'

export default function BarcodeScanner({ onDetected, onClose }) {
  const [error, setError] = useState(null)
  const scannerRef = useRef(null)

  useEffect(() => {
    const scanner = new Html5QrcodeScanner(
      "reader",
      {
        fps: 30,
        qrbox: { width: 280, height: 200 },
        aspectRatio: 1.333,
        showTorchButtonIfSupported: true,
        showZoomSliderIfSupported: true,
        defaultZoomValueIfSupported: 2,
        formatsToSupport: ['CODE_128', 'EAN_13', 'EAN_8', 'UPC_A', 'UPC_E', 'CODE_39', 'CODABAR']
      },
      false
    )

    scannerRef.current = scanner

    const success = (decodedText) => {
      scanner.pause(true)
      onDetected(decodedText)
    }

    scanner.render(success, (err) => {})

    return () => {
      if (scannerRef.current) {
        scannerRef.current.clear()
      }
    }
  }, [onDetected])

  return (
    <div className="scanner-overlay">
      <div className="scanner-container">
        <div className="scanner-header">
          <h3 className="scanner-title">Scan Barcode</h3>
          <button onClick={onClose} className="scanner-close">✕</button>
        </div>

        <div className="scanner-box">
          <div id="reader"></div>
          <div className="scan-line"></div>
          <div className="scanner-corners">
            <div className="corner top-left"></div>
            <div className="corner top-right"></div>
            <div className="corner bottom-left"></div>
            <div className="corner bottom-right"></div>
          </div>
        </div>

        <p className="scanner-hint">
          Position the barcode inside the frame
        </p>
      </div>
    </div>
  )
}