import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home        from './pages/home';
import Register    from './pages/register';
import Login       from './pages/login';
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