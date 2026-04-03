import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";

function Home() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchProducts = () => {
    fetch("http://127.0.0.1:5000/products")
      .then(res => res.json())
      .then(data => {
        setProducts(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching products:", err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  return (
    <div style={{ background: "#f5f5f5", minHeight: "100vh" }}>

      {/* Navbar */}
      <div style={{
        background: "#131921",
        color: "white",
        padding: "15px",
        fontSize: "22px",
        fontWeight: "bold",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center"
      }}>
        🛒 Fashion Store

        <div>
          <Link to="/login" style={{ marginRight: "10px", color: "white" }}>Login</Link>
          <Link to="/register" style={{ marginRight: "10px", color: "white" }}>Register</Link>
          <Link to="/admin">
            <button style={{
              padding: "6px 12px",
              cursor: "pointer",
              borderRadius: "5px",
              border: "none",
              background: "#febd69"
            }}>
              Admin
            </button>
          </Link>
        </div>
      </div>

      {/* Loading */}
      {loading && <h2 style={{ textAlign: "center" }}>Loading...</h2>}

      {/* Empty State */}
      {!loading && products.length === 0 && (
        <p style={{ textAlign: "center" }}>No products found</p>
      )}

      {/* Product Grid */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(200px,1fr))",
        gap: "20px",
        padding: "20px"
      }}>

        {products.map(product => (
          <Link
            to={`/product/${product.id}`}
            key={product.id}
            style={{ textDecoration: "none", color: "inherit" }}
          >
            <div style={{
              background: "white",
              borderRadius: "10px",
              padding: "12px",
              boxShadow: "0 3px 8px rgba(0,0,0,0.1)",
              transition: "0.3s"
            }}>

              {/* Image */}
              <img
                src={`http://127.0.0.1:5000/${product.image_url}`}
                alt={product.name}
                style={{
                  width: "100%",
                  maxHeight: "150px",
                  objectFit: "contain",
                  borderRadius: "8px"
                }}
              />

              {/* Name */}
              <h4 style={{
                fontSize: "14px",
                marginTop: "10px",
                height: "35px",
                overflow: "hidden"
              }}>
                {product.name}
              </h4>

              {/* Brand */}
              <p style={{ fontSize: "12px", color: "gray" }}>
                {product.brand}
              </p>

              {/* Description */}
              <p style={{
                fontSize: "12px",
                color: "#555",
                height: "30px",
                overflow: "hidden"
              }}>
                {product.description}
              </p>

              {/* Price + Rating */}
              <div style={{
                display: "flex",
                justifyContent: "space-between",
                marginTop: "8px"
              }}>
                <span style={{ color: "green", fontWeight: "bold" }}>
                  ₹{product.price ? product.price.toLocaleString() : "N/A"}
                </span>

                <span style={{ fontSize: "12px", color: "#ffa41c" }}>
                  ⭐ {product.rating}
                </span>
              </div>

              {/* Button */}
              <button
                onClick={(e) => {
                  e.preventDefault(); // prevent navigation
                  console.log("Add to cart:", product);
                }}
                disabled={product.stock === 0}
                style={{
                  width: "100%",
                  marginTop: "8px",
                  background: product.stock === 0 ? "gray" : "#ff9900",
                  border: "none",
                  padding: "6px",
                  borderRadius: "5px",
                  color: "white",
                  fontWeight: "bold",
                  cursor: "pointer"
                }}
              >
                {product.stock === 0 ? "Out of Stock" : "Add to Cart"}
              </button>

            </div>
          </Link>
        ))}

      </div>
    </div>
  );
}

export default Home;