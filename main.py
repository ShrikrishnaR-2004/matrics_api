import os
import time
import uuid
import yaml
import jwt
from jwt import InvalidTokenError
from dotenv import dotenv_values
from fastapi import FastAPI, Request, Body
from fastapi.responses import JSONResponse

app = FastAPI()

# =========================================================
# CORS + required headers — ONE middleware, handles everything
# =========================================================
ALLOWED_ORIGIN = "https://dash-4zh4el.example.com"

@app.middleware("http")
async def cors_and_headers(request: Request, call_next):
    start = time.time()
    request_id = str(uuid.uuid4())
    origin = request.headers.get("origin")
    path = request.url.path

    if request.method == "OPTIONS":
        response = JSONResponse(content={})
    else:
        response = await call_next(request)

    duration = time.time() - start
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{duration:.6f}"

    if path == "/stats":
        # STRICT: only the exact assigned origin gets the header.
        # Every other origin (including evil ones) gets NOTHING.
        if origin == ALLOWED_ORIGIN:
            response.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN
            response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
        # else: deliberately add nothing at all
    else:
        # /effective-config, /verify, etc: open to any origin
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"

    return response


# =========================================================
# PART 1: GET /stats
# =========================================================
@app.get("/stats")
def get_stats(values: str):
    nums = [int(v.strip()) for v in values.split(",") if v.strip() != ""]

    count = len(nums)
    total = sum(nums)
    mean = total / count if count > 0 else 0

    return {
        "email": "25ds1000003@ds.study.iitm.ac.in",
        "count": count,
        "sum": total,
        "min": min(nums) if nums else None,
        "max": max(nums) if nums else None,
        "mean": mean,
    }


# =========================================================
# PART 2: POST /verify
# =========================================================
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
        claims = jwt.decode(
            token,
            PUBLIC_KEY,
            algorithms=["RS256"],
            audience=AUDIENCE,
            issuer=ISSUER,
        )
    except InvalidTokenError:
        return JSONResponse(status_code=401, content={"valid": False})

    return {
        "valid": True,
        "email": claims.get("email"),
        "sub": claims.get("sub"),
        "aud": claims.get("aud"),
    }


# =========================================================
# PART 3: GET /effective-config
# =========================================================
DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

def load_yaml_layer():
    try:
        with open("config.development.yaml") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}

def load_dotenv_layer():
    raw = dotenv_values(".env")
    result = {}
    for key, value in raw.items():
        if key == "NUM_WORKERS":
            result["workers"] = value
        elif key.startswith("APP_"):
            clean_key = key[len("APP_"):].lower()
            result[clean_key] = value
    return result

def load_os_env_layer():
    result = {}
    for key, value in os.environ.items():
        if key.startswith("APP_"):
            clean_key = key[len("APP_"):].lower()
            result[clean_key] = value
    return result

def coerce(key, value):
    if key in ("port", "workers"):
        return int(value)
    if key == "debug":
        return str(value).strip().lower() in ("true", "1", "yes", "on")
    return str(value)

@app.get("/effective-config")
def effective_config(request: Request):
    merged = {}
    merged.update(DEFAULTS)
    merged.update(load_yaml_layer())
    merged.update(load_dotenv_layer())
    merged.update(load_os_env_layer())

    for raw in request.query_params.getlist("set"):
        if "=" in raw:
            k, v = raw.split("=", 1)
            merged[k.strip()] = v.strip()

    final = {k: coerce(k, v) for k, v in merged.items()}
    final["api_key"] = "****"

    return final