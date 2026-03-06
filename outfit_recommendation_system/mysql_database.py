from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

# ==============================================================================
# MySQL CONFIGURATION
# Update this connection string with your actual MySQL server credentials:
# Format => mysql+pymysql://<user>:<password>@<host>:<port>/<dbname>
# ==============================================================================
DATABASE_URL = "mysql+pymysql://root:mallikarjun@localhost:3306/smart_outfit_db"

try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    print(f"Failed to initialize MySQL Connection string: {e}")

Base = declarative_base()

# ==============================================================================
# 1. User Authentication Table
# ==============================================================================
class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=True)
    email = Column(String(100), unique=True, index=True, nullable=True)
    phone_number = Column(String(20), unique=True, index=True, nullable=True)
    password = Column(String(255), nullable=True) # Optional since we use OTP
    otp_code = Column(String(10), nullable=True)
    otp_expiry = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# ==============================================================================
# 2. User Preferences Table
# ==============================================================================
class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    preference_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    gender = Column(String(20))
    preferred_style = Column(String(50))
    color_preference = Column(String(50))
    favorite_brand = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

# ==============================================================================
# 3. Products Table (Aggregated from E-Commerce)
# ==============================================================================
class Product(Base):
    __tablename__ = "products"
    
    product_id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(255))
    brand = Column(String(100))
    category = Column(String(50)) # topwear, bottomwear, footwear, accessories
    price = Column(Float)
    rating = Column(Float)
    image_url = Column(String(500))
    product_link = Column(String(500))
    website_source = Column(String(50)) # Myntra, Ajio, Nykaa, Amazon, Flipkart
    created_at = Column(DateTime, default=datetime.utcnow)

# ==============================================================================
# 4. Outfit Recommendations Table
# ==============================================================================
class OutfitRecommendation(Base):
    __tablename__ = "outfit_recommendations"
    
    recommendation_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    outfit_category = Column(String(50))
    score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

# ==============================================================================
# 5. Search History Table
# ==============================================================================
class SearchHistory(Base):
    __tablename__ = "search_history"
    
    search_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    occasion = Column(String(100))
    weather = Column(String(50))
    style = Column(String(50))
    color_preference = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

# ==============================================================================
# 6. Trending Products Table
# ==============================================================================
class TrendingProduct(Base):
    __tablename__ = "trending_products"
    
    trending_id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    popularity_score = Column(Float)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Generate MySQL tables safely based on schema defined above
def init_mysql_db():
    try:
        Base.metadata.create_all(bind=engine)
        print("MySQL Schema successfully synced to db!")
    except Exception as e:
        print(f"Skipping MySQL sync (Server not reachable or missing db): {e}")

if __name__ == "__main__":
    init_mysql_db()
