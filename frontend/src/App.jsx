import { useEffect, useState } from "react";
import { Routes, Route, Link } from "react-router-dom";
import Admin from "./Admin";

function Home() {

  const [products, setProducts] = useState([]);

const fetchProducts = () => {
  fetch("http://127.0.0.1:5000/products")
    .then(res => res.json())
    .then(data => setProducts(data));
};

useEffect(() => {
  fetchProducts();
}, []);

  return (
    <div style={{background:"#f5f5f5", minHeight:"100vh"}}>

      {/* Navbar */}
      <div style={{
        background:"#131921",
        color:"white",
        padding:"15px",
        fontSize:"22px",
        fontWeight:"bold",
        textAlign:"center"
      }}>
        🛒 Fashion Store

        <Link to="/admin">
          <button style={{
            marginLeft:"20px",
            padding:"5px 10px",
            cursor:"pointer"
          }}>
            Admin
          </button>
        </Link>
      </div>

      {/* Product Grid */}
      <div style={{
        display:"grid",
        gridTemplateColumns:"repeat(auto-fill, minmax(180px,1fr))",
        gap:"15px",
        padding:"20px"
      }}>

        {products.map(product => (

          <div key={product.id} style={{
            background:"white",
            borderRadius:"8px",
            padding:"10px",
            boxShadow:"0 2px 5px rgba(0,0,0,0.1)"
          }}>

           <img
  src={product.image_url || "https://via.placeholder.com/200"}
  alt={product.name}
  style={{
    width:"100%",
    height:"120px",
    objectFit:"cover",
    borderRadius:"5px"
  }}
/>

            <h4 style={{
              fontSize:"14px",
              marginTop:"8px",
              height:"35px",
              overflow:"hidden"
            }}>
              {product.name}
            </h4>

            <p style={{
              fontSize:"12px",
              color:"gray",
              height:"30px",
              overflow:"hidden"
            }}>
              {product.description}
            </p>

            <div style={{
              display:"flex",
              justifyContent:"space-between",
              alignItems:"center",
              marginTop:"5px"
            }}>

              <span style={{
                color:"green",
                fontWeight:"bold"
              }}>
                ₹{product.price}
              </span>
              <p style={{fontSize:"12px", color:"#ffa41c"}}>
  ⭐ {product.rating}
</p>
           <button
  disabled={product.stock === 0}
  style={{
    background: product.stock === 0 ? "gray" : "#ff9900",
    border:"none",
    padding:"5px 8px",
    borderRadius:"4px",
    cursor:"pointer",
    fontSize:"12px"
  }}
>
  {product.stock === 0 ? "Out of Stock" : "Add"}
</button>

            </div>

          </div>

        ))}

      </div>

    </div>
  );
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home/>} />
      <Route path="/admin" element={<Admin/>} />
    </Routes>
  );
}

export default App;