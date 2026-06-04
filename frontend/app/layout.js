import './globals.css'; 

export const metadata = {
  title: 'TransparentEat — Know What You Consume',
  description: 'AI-powered food product health analysis. Scan any barcode or search any product to see exactly what ingredients do to your body.',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}