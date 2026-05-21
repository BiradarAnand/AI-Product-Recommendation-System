import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home           from './pages/Home';
import Register       from './pages/Register';
import Login          from './pages/Login';
import Cart           from './pages/Cart';
import Wishlist       from './pages/Wishlist';
import ProductDetails from './pages/ProductDetails';
import Admin          from './pages/Admin';
import UnifiedChatbot from './pages/UnifiedChatbot';

export default function App() {
  return (
    <BrowserRouter>
      {/* Floating chatbot widget — visible on every page */}
      <UnifiedChatbot />

      <Routes>
        <Route path="/"               element={<Home />} />
        <Route path="/register"       element={<Register />} />
        <Route path="/login"          element={<Login />} />
        <Route path="/cart"           element={<Cart />} />
        <Route path="/wishlist"       element={<Wishlist />} />
        <Route path="/product/:id"    element={<ProductDetails />} />
        <Route path="/admin"          element={<Admin />} />
        {/* /occasion-chatbot just opens the chatbot widget — redirect to home */}
        <Route path="/occasion-chatbot" element={<Home />} />
      </Routes>
    </BrowserRouter>
  );
}