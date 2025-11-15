import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Product

app = FastAPI(title="ShopEasy API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "ShopEasy backend is running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

# --------- Product Endpoints ---------
class ProductCreate(Product):
    pass

@app.post("/api/products")
def create_product(product: ProductCreate):
    try:
        inserted_id = create_document("product", product)
        return {"id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/products")
def list_products(category: Optional[str] = None, q: Optional[str] = None, limit: int = 50):
    try:
        filter_dict = {}
        if category:
            filter_dict["category"] = category
        if q:
            # Basic text search across a couple fields
            filter_dict["$or"] = [
                {"title": {"$regex": q, "$options": "i"}},
                {"description": {"$regex": q, "$options": "i"}}
            ]
        docs = get_documents("product", filter_dict, limit=limit)
        # Convert ObjectId to str
        for d in docs:
            if isinstance(d.get("_id"), ObjectId):
                d["id"] = str(d.pop("_id"))
        return {"items": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Seed a few demo products if collection is empty
@app.post("/api/seed")
def seed_products():
    try:
        count = db["product"].count_documents({}) if db is not None else 0
        if count > 0:
            return {"seeded": False, "message": "Products already exist"}
        demo_items = [
            {
                "title": "Wireless Noise-Canceling Headphones",
                "description": "Premium over-ear headphones with 30h battery and ANC.",
                "price": 199.99,
                "category": "Electronics",
                "in_stock": True,
                "brand": "SoundMax",
                "image_url": "https://images.unsplash.com/photo-1518443751420-7e1b34b09b91?q=80&w=1200&auto=format&fit=crop",
                "rating": 4.6,
                "reviews_count": 321,
            },
            {
                "title": "Smart Fitness Watch",
                "description": "Track health metrics with AMOLED display and GPS.",
                "price": 129.0,
                "category": "Wearables",
                "in_stock": True,
                "brand": "FitPulse",
                "image_url": "https://images.unsplash.com/photo-1511732351157-1865efcb7b7b?q=80&w=1200&auto=format&fit=crop",
                "rating": 4.4,
                "reviews_count": 189,
            },
            {
                "title": "Ergonomic Office Chair",
                "description": "Adjustable lumbar support, breathable mesh, smooth wheels.",
                "price": 249.5,
                "category": "Furniture",
                "in_stock": True,
                "brand": "ErgoSeat",
                "image_url": "https://images.unsplash.com/photo-1503602642458-232111445657?q=80&w=1200&auto=format&fit=crop",
                "rating": 4.5,
                "reviews_count": 97,
            },
            {
                "title": "Stainless Steel Water Bottle",
                "description": "Insulated 1L bottle keeps drinks cold for 24h.",
                "price": 24.99,
                "category": "Outdoors",
                "in_stock": True,
                "brand": "AquaPro",
                "image_url": "https://images.unsplash.com/photo-1526405078732-81b3b1b12f39?q=80&w=1200&auto=format&fit=crop",
                "rating": 4.8,
                "reviews_count": 512,
            },
        ]
        for item in demo_items:
            create_document("product", item)
        return {"seeded": True, "count": len(demo_items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
