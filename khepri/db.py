"""
khepri/db.py — Supabase client for the KHEPRI Witness Store.

Uses the supabase-py library with the service-role key so that RLS
insert policies are satisfied without requiring an authenticated user
session.  The client is created once at module import time and shared
across all requests (thread-safe for async FastAPI workloads).

Required environment variables:
    SUPABASE_URL          — project URL  (e.g. https://<ref>.supabase.co)
    SUPABASE_SERVICE_KEY  — service-role secret key (not the anon key)
"""

import os

from supabase import create_client, Client

_url: str = os.environ["SUPABASE_URL"]
_key: str = os.environ["SUPABASE_SERVICE_KEY"]

# Singleton client — created once, reused for every request.
supabase: Client = create_client(_url, _key)
