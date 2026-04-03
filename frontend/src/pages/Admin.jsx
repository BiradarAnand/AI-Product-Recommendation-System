import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

function Admin(){

const navigate = useNavigate();

const [products,setProducts] = useState([]);

const [product,setProduct] = useState({
  name:"",
  description:"",
  category:"",
  brand:"",
  price:"",
  stock:"",
  rating:"",
  reviews:"",
  image_url:""
});

const handleChange = (e)=>{
  setProduct({...product,[e.target.name]:e.target.value});
};

const fetchProducts = ()=>{
  fetch("http://127.0.0.1:5000/products")
  .then(res=>res.json())
  .then(data=>setProducts(data));
};

useEffect(()=>{
  fetchProducts();
},[]);

const addProduct = async () => {

  const res = await fetch("http://127.0.0.1:5000/admin/add-product",{
    method:"POST",
    headers:{
      "Content-Type":"application/json"
    },
    body:JSON.stringify(product)
  });

  const data = await res.json();

  alert(data.message);

  fetchProducts();

  setProduct({
    name:"",
    description:"",
    category:"",
    brand:"",
    price:"",
    stock:"",
    rating:"",
    reviews:"",
    image_url:""
  });

};

const deleteProduct = async(id)=>{

  await fetch(`http://127.0.0.1:5000/admin/delete-product/${id}`,{
    method:"DELETE"
  });

  alert("Product deleted");

  fetchProducts();
};

return(

<div style={{padding:"30px"}}>

<h2>Admin Dashboard</h2>

<button onClick={()=>navigate("/")} style={{marginBottom:"20px"}}>
Back to Store
</button>

{/* ADD PRODUCT FORM */}

<div style={{
  maxWidth:"500px",
  background:"white",
  padding:"20px",
  borderRadius:"8px",
  boxShadow:"0 2px 10px rgba(0,0,0,0.1)"
}}>

<h3>Add Product</h3>

<input name="name" placeholder="Product Name" value={product.name} onChange={handleChange} style={{width:"100%",margin:"5px 0"}}/>

<textarea name="description" placeholder="Description" value={product.description} onChange={handleChange} style={{width:"100%",margin:"5px 0"}}/>

<input name="category" placeholder="Category" value={product.category} onChange={handleChange} style={{width:"100%",margin:"5px 0"}}/>

<input name="brand" placeholder="Brand" value={product.brand} onChange={handleChange} style={{width:"100%",margin:"5px 0"}}/>

<input name="price" placeholder="Price" type="number" value={product.price} onChange={handleChange} style={{width:"100%",margin:"5px 0"}}/>

<input name="stock" placeholder="Stock" type="number" value={product.stock} onChange={handleChange} style={{width:"100%",margin:"5px 0"}}/>

<input name="rating" placeholder="Rating" value={product.rating} onChange={handleChange} style={{width:"100%",margin:"5px 0"}}/>

<input name="reviews" placeholder="Reviews" value={product.reviews} onChange={handleChange} style={{width:"100%",margin:"5px 0"}}/>

<input name="image_url" placeholder="Image URL" value={product.image_url} onChange={handleChange} style={{width:"100%",margin:"5px 0"}}/>

<button onClick={addProduct} style={{
  width:"100%",
  padding:"10px",
  background:"#ff9900",
  border:"none",
  marginTop:"10px",
  cursor:"pointer"
}}>
Add Product
</button>

</div>

{/* PRODUCT LIST */}

<h3 style={{marginTop:"40px"}}>All Products</h3>

<table border="1" cellPadding="10" style={{width:"100%",marginTop:"10px"}}>

<thead>
<tr>
<th>ID</th>
<th>Name</th>
<th>Price</th>
<th>Stock</th>
<th>Image</th>
<th>Action</th>
</tr>
</thead>

<tbody>

{products.map(p=>(
<tr key={p.id}>
<td>{p.id}</td>
<td>{p.name}</td>
<td>₹{p.price}</td>
<td>{p.stock}</td>
<td>
<img src={p.image_url} width="50"/>
</td>
<td>
<button onClick={()=>deleteProduct(p.id)} style={{
  background:"red",
  color:"white",
  border:"none",
  padding:"5px",
  cursor:"pointer"
}}>
Delete
</button>
</td>
</tr>
))}

</tbody>

</table>

</div>

);
}

export default Admin;