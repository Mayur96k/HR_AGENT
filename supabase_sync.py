"""
supabase_sync.py — Optional: Push results to Supabase (used by the HTML dashboard)
"""
import logging
import httpx

log = logging.getLogger(__name__)


async def push_results(results: list, supabase_url: str, supabase_key: str):
    """Push scored results to Supabase candidates table."""
    if not supabase_url or not supabase_key:
        log.info("Supabase not configured — skipping DB sync")
        return

    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    url = f"{supabase_url}/rest/v1/candidates"
    success = 0

    async with httpx.AsyncClient(timeout=30) as client:
        for r in results:
            try:
                resp = await client.post(url, headers=headers, json=r)
                if resp.status_code in (200, 201):
                    success += 1
                else:
                    log.warning(f"Supabase insert failed: {resp.status_code} {resp.text[:100]}")
            except Exception as e:
                log.error(f"Supabase error: {e}")

    log.info(f"Supabase: {success}/{len(results)} records synced")
