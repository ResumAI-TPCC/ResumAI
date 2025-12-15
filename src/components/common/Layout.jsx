import Navbar from './Navbar'
import Footer from './Footer'
import './Layout.css'

function Layout({ children }) {
  return (
    <div className="layout">
      <Navbar />
      <main className="main-content">
        {children}
      </main>
      <Footer />
    </div>
  )
}

export default Layout

