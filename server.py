"""
MCP Server: Ansible Automation Platform (AAP) connector for Claude/Inspector
"""

import os, sys, warnings, logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import Context, FastMCP

# ---- ABSOLUTE RULE: stdout must be JSON-RPC only ----
# Route all logs to stderr
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
log = logging.getLogger("mcp-aap")

# Silence Python warnings to stderr (not stdout)
warnings.simplefilter("default")
os.environ.setdefault("PYTHONWARNINGS", "default")

# Load .env quietly
load_dotenv()

# ------------------------- Config -------------------------
@dataclass
class AAPConfig:
    base_url: str = ""
    token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    verify_ssl: bool = True
    timeout_sec: int = 30

    @classmethod
    def from_env(cls) -> "AAPConfig":
        base_url = os.getenv("AAP_BASE_URL", "").rstrip("/")
        token = os.getenv("AAP_TOKEN") or None
        username = os.getenv("AAP_USERNAME") or None
        password = os.getenv("AAP_PASSWORD") or None
        verify_str = (os.getenv("AAP_VERIFY_SSL", "true") or "true").lower()
        verify_ssl = verify_str in ("1", "true", "yes", "y")
        try:
            timeout_sec = int(os.getenv("AAP_TIMEOUT_SEC", "30"))
        except Exception:
            timeout_sec = 30
        return cls(base_url, token, username, password, verify_ssl, timeout_sec)

# ------------------------- Client -------------------------
class AAPClient:
    def __init__(self, cfg: AAPConfig):
        if not cfg.base_url:
            raise RuntimeError(
                "AAP_BASE_URL is not set. Provide .env with AAP_BASE_URL and either AAP_TOKEN "
                "or AAP_USERNAME/AAP_PASSWORD."
            )
        headers = {"Content-Type": "application/json"}
        if cfg.token:
            headers["Authorization"] = f"Bearer {cfg.token}"
        self._client = httpx.Client(
            base_url=f"{cfg.base_url}/api/v2",
            headers=headers,
            verify=cfg.verify_ssl,
            timeout=cfg.timeout_sec,
        )
        if not cfg.token and cfg.username and cfg.password:
            self._client.auth = (cfg.username, cfg.password)

    @staticmethod
    def _raise_for_status(resp: httpx.Response) -> None:
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            # Return clean JSON-RPC error to the Inspector
            raise RuntimeError(
                f"AAP API error {resp.status_code} at {resp.request.url}: {resp.text}"
            ) from e

    def _post(self, path: str, payload: Optional[dict] = None) -> httpx.Response:
        resp = self._client.post(path, json=payload or {})
        self._raise_for_status(resp)
        return resp

    def _get(self, path: str, params: Optional[dict] = None) -> httpx.Response:
        resp = self._client.get(path, params=params)
        self._raise_for_status(resp)
        return resp

    # ---- Job Templates ----
    def list_job_templates(self, search: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {"page_size": 100}
        if search:
            params["search"] = search
        data = self._get("/job_templates/", params=params).json()
        return data.get("results", data if isinstance(data, list) else [])

    def create_job_template(
        self, name: str, project_id: int, inventory_id: int, playbook: str
    ) -> Dict[str, Any]:
        payload = {
            "name": name,
            "job_type": "run",
            "project": project_id,
            "inventory": inventory_id,
            "playbook": playbook,
        }
        resp = self._client.post("/job_templates/", json=payload)
        self._raise_for_status(resp)
        return resp.json()

    def launch_job_template(
        self, template_id: int, extra_vars: Optional[dict] = None
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if extra_vars:
            payload["extra_vars"] = extra_vars
        return self._post(f"/job_templates/{template_id}/launch/", payload).json()

    # ---- Jobs ----
    def get_job(self, job_id: int) -> Dict[str, Any]:
        return self._get(f"/jobs/{job_id}/").json()

    def get_job_stdout(self, job_id: int) -> str:
        return self._get(f"/jobs/{job_id}/stdout/", params={"format": "txt"}).text

    def close(self) -> None:
        try:
            self._client.close()
        except Exception:
            pass

# ------------------------- Lifespan -------------------------
@dataclass
class AppCtx:
    cfg: AAPConfig

@asynccontextmanager
async def lifespan(server: FastMCP):
    # Do NOT initialize network clients here; keep startup silent & deterministic
    yield AppCtx(cfg=AAPConfig.from_env())

mcp = FastMCP("Ansible Automation Platform", lifespan=lifespan)

# ------------------------- Helpers -------------------------
def _build_client(ctx: Context) -> AAPClient:
    app: AppCtx = ctx.request_context.lifespan_context
    return AAPClient(app.cfg)  # build per call, safe for JSON-RPC errors

# ------------------------- Tools -------------------------
@mcp.tool(description="List job templates; optional fuzzy search")
def list_job_templates(ctx: Context, search: Optional[str] = None):
    return _build_client(ctx).list_job_templates(search)

@mcp.tool(description="Create a minimal job template")
def create_job_template(
    ctx: Context, name: str, project_id: int, inventory_id: int, playbook: str
):
    return _build_client(ctx).create_job_template(name, project_id, inventory_id, playbook)

@mcp.tool(description="Launch a job template; supports extra_vars")
def launch_job(
    ctx: Context, template_id: int, extra_vars: Optional[Dict[str, Any]] = None
):
    return _build_client(ctx).launch_job_template(template_id, extra_vars=extra_vars)

@mcp.tool(description="Get job status/metadata by job_id")
def get_job_status(ctx: Context, job_id: int):
    return _build_client(ctx).get_job(job_id)

@mcp.tool(description="Fetch job stdout as plain text")
def get_job_stdout(ctx: Context, job_id: int):
    return _build_client(ctx).get_job_stdout(job_id)

# ------------------------- Entrypoint -------------------------
if __name__ == "__main__":
    try:
        mcp.run()
    except Exception as e:
        # log to stderr; never stdout
        log.exception("Fatal error in MCP server: %s", e)
        sys.exit(1)
