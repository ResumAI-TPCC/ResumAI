import { Link } from 'react-router-dom'
import './Navbar.css'

function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-brand">
          <span className="brand-icon">✨</span>
          <span className="brand-text">ResumAI</span>
        </Link>
        <div className="navbar-links">
          <Link to="/" className="nav-link">Home</Link>
        </div>
      </div>
    </nav>
  )
}

export default Navbar

