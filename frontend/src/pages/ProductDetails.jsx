import { useEffect, useState } from "react";

function ProductList() {
  const [products, setProducts] = useState([]);

  useEffect(() => {
    fetch("http://127.0.0.1:5000/products")
      .then(res => res.json())
      .then(data => setProducts(data))
      .catch(err => console.error(err));
  }, []);

  return (
    <div style={{ padding: "20px", background: "#f5f5f5" }}>
      
      <h2 style={{ textAlign: "center" }}>Products</h2>

      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
        gap: "20px"
      }}>

        {products.map(item => (
          <div key={item.id} style={{
            background: "#fff",
            padding: "15px",
            borderRadius: "10px",
            boxShadow: "0 2px 8px rgba(0,0,0,0.1)"
          }}>

            {/* Image */}
            <img
              src={`http://127.0.0.1:5000/${item.image_url}`}
              alt={item.name}
              style={{ width: "100%", height: "200px", objectFit: "cover" }}
            />

            {/* Details */}
            <h4>{item.name}</h4>
            <p style={{ color: "gray" }}>{item.brand}</p>
            <p><b>₹{item.price}</b></p>
            <p>⭐ {item.rating} ({item.reviews})</p>

          </div>
        ))}

      </div>
    </div>
  );
}

export default ProductList;