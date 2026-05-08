import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home        from './pages/Home';
import Register    from './pages/Register';
import Login       from './pages/Login';
import Cart        from './pages/Cart';
import Wishlist    from './pages/Wishlist';
import UnifiedChatbot from './pages/UnifiedChatbot'; // ← your merged chatbot file

export default function App() {
  return (
    <BrowserRouter>

      {/* ── Floating chatbot widget — visible on EVERY page ── */}
      <UnifiedChatbot />

      <Routes>
        <Route path="/"          element={<Home />} />
        <Route path="/register"  element={<Register />} />
        <Route path="/login"     element={<Login />} />
        <Route path="/cart"      element={<Cart />} />
        <Route path="/wishlist"  element={<Wishlist />} />
      </Routes>

    </BrowserRouter>
  );
}