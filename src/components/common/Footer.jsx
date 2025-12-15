import './Footer.css'

function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="footer">
      <div className="footer-container">
        <div className="footer-brand">
          <span className="footer-logo">✨ ResumAI</span>
          <p className="footer-tagline">Build your future, one resume at a time</p>
        </div>
        <div className="footer-bottom">
          <p>&copy; {currentYear} ResumAI. All rights reserved.</p>
        </div>
      </div>
    </footer>
  )
}

export default Footer

