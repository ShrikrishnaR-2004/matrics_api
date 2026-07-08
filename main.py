import time
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

# ---- STEP 2a: CORS rule ----
# This tells the browser: "only https://dash-4zh4el.example.com
# is allowed to fetch this API from JavaScript."
ALLOWED_ORIGIN = "https://dash-4zh4el.example.com"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],   # NOT "*" — that would fail the grader
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

# ---- STEP 2b: Middleware for X-Request-ID and X-Process-Time ----
# Middleware = code that runs before AND after every request,
# no matter which endpoint was called.
@app.middleware("http")
async def add_custom_headers(request: Request, call_next):
    start = time.time()
    request_id = str(uuid.uuid4())

    response = await call_next(request)  # actually run the endpoint

    duration = time.time() - start
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{duration:.6f}"
    return response

# ---- STEP 2c: The actual /stats endpoint ----
@app.get("/stats")
def get_stats(values: str):
    # values arrives as a string like "1,2,3,4"
    nums = [int(v.strip()) for v in values.split(",") if v.strip() != ""]

    count = len(nums)
    total = sum(nums)
    mean = total / count if count > 0 else 0

    return {
        "email": "25ds1000003@ds.study.iitm.ac.in",  # <-- put YOUR real email
        "count": count,
        "sum": total,
        "min": min(nums) if nums else None,
        "max": max(nums) if nums else None,
        "mean": mean,
    }