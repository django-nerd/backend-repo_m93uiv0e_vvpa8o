import os
from typing import List, Optional, Any, Dict
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId
from datetime import datetime, timedelta, timezone

from database import db, create_document, get_documents
from schemas import User as UserSchema, HouseCategory as HouseCategorySchema, Subcategory as SubcategorySchema, Package as PackageSchema, Quotation as QuotationSchema

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helpers
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

def to_str_id(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not doc:
        return doc
    doc["_id"] = str(doc["_id"]) if "_id" in doc else None
    # Convert datetime to isoformat
    for k, v in list(doc.items()):
        if isinstance(v, datetime):
            doc[k] = v.isoformat()
    return doc

# Root and health
@app.get("/")
def read_root():
    return {"message": "Interior Design Quotation API"}

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
            response["database"] = "✅ Connected & Working"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = getattr(db, "name", None) or ""
            response["connection_status"] = "Connected"
            try:
                response["collections"] = db.list_collection_names()
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "❌ Database not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# Generic CRUD utilities

def insert_with_schema(collection: str, data: BaseModel):
    new_id = create_document(collection, data)
    doc = db[collection].find_one({"_id": ObjectId(new_id)})
    return to_str_id(doc)

def update_by_id(collection: str, _id: str, payload: dict):
    if not ObjectId.is_valid(_id):
        raise HTTPException(status_code=400, detail="Invalid id")
    payload["updated_at"] = datetime.now(timezone.utc)
    res = db[collection].find_one_and_update({"_id": ObjectId(_id)}, {"$set": payload}, return_document=True)
    if not res:
        raise HTTPException(status_code=404, detail="Not found")
    return to_str_id(res)

def delete_by_id(collection: str, _id: str):
    if not ObjectId.is_valid(_id):
        raise HTTPException(status_code=400, detail="Invalid id")
    res = db[collection].delete_one({"_id": ObjectId(_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return {"deleted": True}

# Users
@app.get("/api/users")
def list_users(role: Optional[str] = Query(None)):
    q = {"role": role} if role else {}
    docs = db["user"].find(q).sort("created_at", -1)
    return [to_str_id(d) for d in docs]

@app.post("/api/users", status_code=201)
def create_user(user: UserSchema):
    return insert_with_schema("user", user)

@app.put("/api/users/{user_id}")
def update_user(user_id: str, payload: dict):
    return update_by_id("user", user_id, payload)

@app.delete("/api/users/{user_id}")
def delete_user(user_id: str):
    return delete_by_id("user", user_id)

# House Categories
@app.get("/api/categories")
def list_categories():
    docs = db["housecategory"].find().sort("created_at", -1)
    return [to_str_id(d) for d in docs]

@app.post("/api/categories", status_code=201)
def create_category(category: HouseCategorySchema):
    return insert_with_schema("housecategory", category)

@app.put("/api/categories/{category_id}")
def update_category(category_id: str, payload: dict):
    return update_by_id("housecategory", category_id, payload)

@app.delete("/api/categories/{category_id}")
def delete_category(category_id: str):
    return delete_by_id("housecategory", category_id)

# Subcategories
@app.get("/api/subcategories")
def list_subcategories(category_id: Optional[str] = Query(None)):
    q = {"category_id": category_id} if category_id else {}
    docs = db["subcategory"].find(q).sort("created_at", -1)
    return [to_str_id(d) for d in docs]

@app.post("/api/subcategories", status_code=201)
def create_subcategory(sub: SubcategorySchema):
    # Validate category id format
    if not ObjectId.is_valid(sub.category_id):
        raise HTTPException(status_code=400, detail="Invalid category_id")
    return insert_with_schema("subcategory", sub)

@app.put("/api/subcategories/{sub_id}")
def update_subcategory(sub_id: str, payload: dict):
    return update_by_id("subcategory", sub_id, payload)

@app.delete("/api/subcategories/{sub_id}")
def delete_subcategory(sub_id: str):
    return delete_by_id("subcategory", sub_id)

# Packages
@app.get("/api/packages")
def list_packages(category_id: Optional[str] = Query(None), subcategory_id: Optional[str] = Query(None)):
    q: Dict[str, Any] = {}
    if category_id:
        q["category_id"] = category_id
    if subcategory_id:
        q["subcategory_id"] = subcategory_id
    docs = db["package"].find(q).sort("created_at", -1)
    return [to_str_id(d) for d in docs]

@app.post("/api/packages", status_code=201)
def create_package(pkg: PackageSchema):
    if pkg.category_id and not ObjectId.is_valid(pkg.category_id):
        raise HTTPException(status_code=400, detail="Invalid category_id")
    if pkg.subcategory_id and not ObjectId.is_valid(pkg.subcategory_id):
        raise HTTPException(status_code=400, detail="Invalid subcategory_id")
    return insert_with_schema("package", pkg)

@app.put("/api/packages/{package_id}")
def update_package(package_id: str, payload: dict):
    return update_by_id("package", package_id, payload)

@app.delete("/api/packages/{package_id}")
def delete_package(package_id: str):
    return delete_by_id("package", package_id)

# Quotations
@app.get("/api/quotations")
def list_quotations(employee_id: Optional[str] = Query(None), status: Optional[str] = Query(None)):
    q: Dict[str, Any] = {}
    if employee_id:
        q["employee_id"] = employee_id
    if status:
        q["status"] = status
    docs = db["quotation"].find(q).sort("created_at", -1)
    return [to_str_id(d) for d in docs]

@app.get("/api/quotations/{quotation_id}")
def get_quotation(quotation_id: str):
    if not ObjectId.is_valid(quotation_id):
        raise HTTPException(status_code=400, detail="Invalid id")
    doc = db["quotation"].find_one({"_id": ObjectId(quotation_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    return to_str_id(doc)

@app.post("/api/quotations", status_code=201)
def create_quotation(quotation: QuotationSchema):
    # Basic validation
    if not ObjectId.is_valid(quotation.employee_id):
        raise HTTPException(status_code=400, detail="Invalid employee_id")
    if quotation.house_category_id and not ObjectId.is_valid(quotation.house_category_id):
        raise HTTPException(status_code=400, detail="Invalid house_category_id")
    if quotation.subcategory_id and not ObjectId.is_valid(quotation.subcategory_id):
        raise HTTPException(status_code=400, detail="Invalid subcategory_id")
    # Calculate totals if needed
    subtotal = sum([item.total for item in quotation.items]) if quotation.items else 0
    if quotation.subtotal == 0 and subtotal:
        payload = quotation.model_dump()
        payload["subtotal"] = subtotal
        payload["total"] = subtotal - quotation.discount + quotation.tax
        new_id = create_document("quotation", payload)
    else:
        new_id = create_document("quotation", quotation)
    doc = db["quotation"].find_one({"_id": ObjectId(new_id)})
    return to_str_id(doc)

@app.put("/api/quotations/{quotation_id}")
def update_quotation(quotation_id: str, payload: dict):
    return update_by_id("quotation", quotation_id, payload)

@app.delete("/api/quotations/{quotation_id}")
def delete_quotation(quotation_id: str):
    return delete_by_id("quotation", quotation_id)

# Performance summary for employee dashboard
@app.get("/api/performance")
def performance(employee_id: str = Query(...)):
    if not ObjectId.is_valid(employee_id):
        raise HTTPException(status_code=400, detail="Invalid employee_id")
    q = {"employee_id": employee_id}
    total_quotes = db["quotation"].count_documents(q)
    last30 = datetime.now(timezone.utc) - timedelta(days=30)
    last30_quotes = db["quotation"].count_documents({**q, "created_at": {"$gte": last30}})
    agg = db["quotation"].aggregate([
        {"$match": q},
        {"$group": {"_id": None, "revenue": {"$sum": "$total"}, "avg": {"$avg": "$total"}}}
    ])
    revenue = 0
    avg = 0
    for a in agg:
        revenue = a.get("revenue", 0)
        avg = a.get("avg", 0)
    return {
        "total_quotations": total_quotes,
        "last30_quotations": last30_quotes,
        "total_revenue": revenue,
        "avg_quote_value": avg
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
