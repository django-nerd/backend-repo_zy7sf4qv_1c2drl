import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Product

app = FastAPI(title="ElectroX API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProductIn(BaseModel):
    title: str
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    category: str
    in_stock: bool = True
    image_url: Optional[str] = None

class ProductOut(ProductIn):
    id: str

@app.get("/")
def read_root():
    return {"message": "ElectroX backend running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from ElectroX API"}

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
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name
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
    return response

# Products Endpoints
@app.post("/api/products", response_model=dict)
def create_product(product: ProductIn):
    try:
        new_id = create_document("product", product)
        return {"id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/products", response_model=List[ProductOut])
def list_products(category: Optional[str] = None, limit: int = 20):
    try:
        filter_dict = {"category": category} if category else {}
        docs = get_documents("product", filter_dict, limit)
        results: List[ProductOut] = []
        for d in docs:
            d["id"] = str(d.get("_id"))
            for k in ["_id", "created_at", "updated_at"]:
                if k in d:
                    del d[k]
            results.append(ProductOut(**d))
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/products/sample", response_model=List[ProductOut])
def sample_products():
    demo = [
        {
            "title": "Gaming Laptop X15",
            "description": "RTX graphics, 16GB RAM, 1TB SSD",
            "price": 1899.99,
            "category": "Laptops",
            "in_stock": True,
            "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8"
        },
        {
            "title": "Wireless Noise-Canceling Headphones",
            "description": "40h battery, ANC, Bluetooth 5.3",
            "price": 249.99,
            "category": "Audio",
            "in_stock": True,
            "image_url": "https://images.unsplash.com/photo-1518444028785-8f6f3117db19"
        },
        {
            "title": "4K Gaming Monitor 27''",
            "description": "144Hz, HDR600, 1ms",
            "price": 499.0,
            "category": "Monitors",
            "in_stock": True,
            "image_url": "https://images.unsplash.com/photo-1518770660439-4636190af475"
        }
    ]
    return [ProductOut(id=str(i), **p) for i, p in enumerate(demo, start=1)]

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
