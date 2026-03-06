# AI-Based Product Recommendation System

## 1. System Architecture
The system architecture defines the high-level structure and components of our platform and their interactions:

```mermaid
flowchart TD
    User([User App / Web Frontend]) <--> MiddleWare{Middleware / API Gateway}
    MiddleWare <--> Backend[Backend API]
    Backend <--> DB[(Database + ML Model \n+ Cloud Storage)]
    Backend <--> RE[Recommendation Engine]
```

## 2. Unified Modeling Language (UML) - Use Cases

### Actors
* **User**: The end-consumer browsing and purchasing products.
* **Admin**: The platform administrator who manages the system.

```mermaid
flowchart LR
    %% Actors
    Admin([Admin])
    Client([User])

    %% Use Cases
    subgraph Admin Panel
        A1(Add Products)
        A2(Manage Users)
        A3(View Reports)
        A4(Manage Orders)
    end
    
    subgraph User Journey
        U1(Register)
        U2(Login)
        U3(Search Product)
        U4(View Recommended Products)
        U5(Add to Cart)
        U6(Make Payment)
    end

    %% Relationships
    Admin --> A1
    Admin --> A2
    Admin --> A3
    Admin --> A4

    Client --> U1
    Client --> U2
    Client --> U3
    Client --> U4
    Client --> U5
    Client --> U6
```

## 3. Sequence Diagram (Login & View Products)

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend as Backend API
    participant RE as Recommendation Engine
    participant DB as Database

    User->>Frontend: Login
    Frontend->>Backend: API Request (Login)
    Backend->>DB: Verify User Credentials
    DB-->>Backend: Return User Data
    Backend-->>Frontend: Success Response
    Frontend-->>User: Display Account/Dashboard
    
    User->>Frontend: View Product
    Frontend->>Backend: API Request
    Backend->>DB: Fetch Product Info
    DB-->>Backend: Product Data
    Backend->>RE: Send User History / Context
    RE-->>Backend: Recommended Products Array
    Backend-->>Frontend: Response (Product + Recommendations)
    Frontend-->>User: Display Product & Recommendations
```

## 4. Class Diagram

*(Note: Based on your provided UML Actors and actions, here is a foundational class structure that connects the entities)*

```mermaid
classDiagram
    class User {
        +int userId
        +string name
        +string email
        +string password
        +register()
        +login()
        +searchProduct()
        +viewRecommended()
        +addToCart()
        +makePayment()
    }

    class Admin {
        +int adminId
        +string role
        +addProducts()
        +manageUsers()
        +viewReports()
        +manageOrders()
    }

    class Product {
        +int productId
        +string title
        +float price
        +string category
        +string imageUrl
        +getDetails()
    }

    class Order {
        +int orderId
        +string status
        +float totalAmount
        +createOrder()
        +updateStatus()
    }

    class RecommendationEngine {
        +int modelVersion
        +generateRecommendations(userId, browsingHistory)
    }

    User "1" -- "*" Order : places
    Admin "1" -- "*" Product : manages
    Order "*" -- "*" Product : contains
    RecommendationEngine "1" -- "*" User : analyzes
    RecommendationEngine "1" -- "*" Product : returns
```
