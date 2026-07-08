import time
import uuid
from fastapi import FastAPI, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import jwt
from jwt import InvalidTokenError

app = FastAPI()

# ---- STEP 2a: CORS rule ----
# This tells the browser: "only https://dash-4zh4el.example.com
# is allowed to fetch this API from JavaScript."
ALLOWED_ORIGIN = "https://dash-4zh4el.example.com"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],   # NOT "*" — that would fail the grader
    allow_methods=["GET", "POST", "OPTIONS"],
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

ISSUER = "https://idp.exam.local"
AUDIENCE = "tds-w8y92f1t.apps.exam.local"

PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY
cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbYGuc3EbNy4xFyf5Cbj5DHJMID
EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc
WyJjG2axVfmq7i6SuKr1JoWYG7xTTAvKPujSl4OtsQfO3h5NepzdfXpr28oNnzfW
ed+zclR6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd1l9VDetJZVEgC5tkyvXsfI
SI6iyrYbKR0NEBSqq4XkadEjsCs4F1RncsS4LlgniT7GlkL9Mce3b0wGLs9/7ZIX
dQIDAQAB
-----END PUBLIC KEY-----"""

@app.post("/verify")
def verify_token(payload: dict = Body(...)):
    token = payload.get("token", "")

    try:
        # jwt.decode() does steps 1-4 all at once when you pass these arguments:
        claims = jwt.decode(
            token,
            PUBLIC_KEY,
            algorithms=["RS256"],   # only accept RS256 — stops "alg confusion" attacks
            audience=AUDIENCE,      # checks aud matches, rejects if not
            issuer=ISSUER,          # checks iss matches, rejects if not
            # exp is checked automatically by pyjwt whenever it's present
        )
    except InvalidTokenError:
        # This catches ALL failure cases: bad signature, expired,
        # wrong audience, wrong issuer, tampered payload — anything wrong.
        return JSONResponse(status_code=401, content={"valid": False})

    # If we get here, every check passed.
    return {
        "valid": True,
        "email": claims.get("email"),
        "sub": claims.get("sub"),
        "aud": claims.get("aud"),
    }
