import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Home           from './pages/Home';
import Register       from './pages/Register';
import Login          from './pages/Login';
import Cart           from './pages/Cart';
import Wishlist       from './pages/Wishlist';
import ProductDetails from './pages/ProductDetails';
import Admin          from './pages/Admin';
import UnifiedChatbot from './pages/UnifiedChatbot';

// ── Protects routes based on role ─────────────────────────────────────────
function ProtectedRoute({ element, allowedRoles }) {
  const user = JSON.parse(localStorage.getItem("user") || "null");

  // Not logged in → go to login
  if (!user) return <Navigate to="/login" replace />;

  // Wrong role → go to home
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/" replace />;
  }

  return element;
}

// ── Redirect logged-in users away from login/register ─────────────────────
function GuestRoute({ element }) {
  const user = JSON.parse(localStorage.getItem("user") || "null");
  if (user) return <Navigate to="/" replace />;
  return element;
}

export default function App() {
  return (
    <BrowserRouter>
      {/* Floating chatbot — visible on every page */}
      <UnifiedChatbot />

      <Routes>
        {/* Public routes */}
        <Route path="/"                 element={<Home />} />
        <Route path="/product/:id"      element={<ProductDetails />} />
        <Route path="/occasion-chatbot" element={<Home />} />

        {/* Guest only — redirect to home if already logged in */}
        <Route path="/login"    element={<GuestRoute element={<Login />} />} />
        <Route path="/register" element={<GuestRoute element={<Register />} />} />

        {/* Logged-in users only */}
        <Route path="/cart"     element={<ProtectedRoute element={<Cart />} />} />
        <Route path="/wishlist" element={<ProtectedRoute element={<Wishlist />} />} />

        {/* Admin only */}
        <Route path="/admin"
          element={<ProtectedRoute element={<Admin />} allowedRoles={["admin"]} />}
        />

        {/* Catch all → home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}