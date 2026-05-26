import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Home           from './pages/Home';
import Register       from './pages/Register';
import Login          from './pages/Login';
import Cart           from './pages/Cart';
import Wishlist       from './pages/Wishlist';
import ProductDetails from './pages/ProductDetails';
import Admin          from './pages/Admin';
import Profile        from './pages/Profile';
import UnifiedChatbot from './pages/UnifiedChatbot';
import { QuickViewProvider } from './components/ProductQuickView';

function ProtectedRoute({ element, allowedRoles }) {
  const user = JSON.parse(localStorage.getItem("user") || "null");
  if (!user) return <Navigate to="/login" replace />;
  if (allowedRoles && !allowedRoles.includes(user.role)) return <Navigate to="/" replace />;
  return element;
}

function GuestRoute({ element }) {
  const user = JSON.parse(localStorage.getItem("user") || "null");
  if (user) return <Navigate to="/" replace />;
  return element;
}

export default function App() {
  return (
    <BrowserRouter>
      <QuickViewProvider>
        <UnifiedChatbot />
        <Routes>
          <Route path="/"                 element={<Home />} />
          <Route path="/product/:id"      element={<ProductDetails />} />
          <Route path="/occasion-chatbot" element={<Home />} />

          <Route path="/login"    element={<GuestRoute element={<Login />} />} />
          <Route path="/register" element={<GuestRoute element={<Register />} />} />

          <Route path="/cart"     element={<ProtectedRoute element={<Cart />} />} />
          <Route path="/wishlist" element={<ProtectedRoute element={<Wishlist />} />} />
          <Route path="/profile"  element={<ProtectedRoute element={<Profile />} />} />

          <Route path="/admin"
            element={<ProtectedRoute element={<Admin />} allowedRoles={["admin"]} />}
          />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </QuickViewProvider>
    </BrowserRouter>
  );
}