import axios from "axios";
import axiosRetry from "axios-retry";
import { config } from "../config.js";

const debug = process.env.HOTELRUNNER_DEBUG_LOG_REQUEST === 'true';
const useBodyHrId = process.env.HOTELRUNNER_USE_BODY_HR_ID === 'true';
const mockMode = process.env.HOTELRUNNER_MOCK_MODE === 'true';

const api = axios.create({
  baseURL: config.hotelrunner.base,
  timeout: 10000,
  headers: {
    Authorization: `Bearer ${config.hotelrunner.token}`,
    "Content-Type": "application/json",
  },
  params: useBodyHrId ? {} : { hr_id: config.hotelrunner.id },
});

axiosRetry(api, {
  retries: 2,
  retryDelay: axiosRetry.exponentialDelay,
  retryCondition: (err) => axiosRetry.isNetworkOrIdempotentRequestError(err) || axiosRetry.isRetryableError(err),
});

// Lightweight circuit breaker
let open = false;
let halfOpen = false;
let nextTry = 0;
const OPEN_FOR_MS = 10_000;
const FAIL_THRESHOLD = 3;
let fails = 0;

function canPass() {
  const now = Date.now();
  if (!open) return true;
  if (now >= nextTry) { halfOpen = true; return true; }
  return false;
}
function onSuccess() { fails = 0; open = false; halfOpen = false; }
function onFailure() {
  fails += 1;
  if (fails >= FAIL_THRESHOLD) {
    open = true; halfOpen = false; nextTry = Date.now() + OPEN_FOR_MS;
  }
}


// Compose payload variants for different HR schemas
function buildPayloadVariants(payload, hrId, useBodyHrId) {
  const base = { ...payload };
  const variants = [];

  // Variant 1: as-is (possibly with hr_id in params or body)
  variants.push(useBodyHrId ? { ...base, hr_id: hrId } : base);

  // Variant 2: checkin/checkout (no underscores)
  variants.push({
    checkin: payload.check_in,
    checkout: payload.check_out,
    adults: payload.adults,
    children: payload.children ?? 0,
    currency: payload.currency ?? "EUR",
    ...(useBodyHrId ? { hr_id: hrId } : {}),
  });

  // Variant 3: start_date / end_date
  variants.push({
    start_date: payload.check_in,
    end_date: payload.check_out,
    adults: payload.adults,
    children: payload.children ?? 0,
    currency: payload.currency ?? "EUR",
    ...(useBodyHrId ? { hr_id: hrId } : {}),
  });

  // Variant 4: occupancy-style
  variants.push({
    date_range: { start: payload.check_in, end: payload.check_out },
    rooms: [{ adults: payload.adults, children: payload.children ?? 0 }],
    currency: payload.currency ?? "EUR",
    ...(useBodyHrId ? { hr_id: hrId } : {}),
  });

  return variants;
}



// --- RAW AVAILABILITY MODE (no /availability/search) ---
// Try multiple date-key pairs per config; fetch raw availability and compute a simple view.
function parseDateKeyPairs(envVal) {
  // Example: "check_in,check_out;checkin,checkout;start_date,end_date"
  const pairs = [];
  const chunks = (envVal || "").split(";").map(s => s.trim()).filter(Boolean);
  for (const c of chunks) {
    const [a,b] = c.split(",").map(s => s.trim());
    if (a && b) pairs.push([a,b]);
  }
  if (pairs.length === 0) pairs.push(["check_in","check_out"]);
  return pairs;
}

export async function getAvailabilityRaw({ check_in, check_out, adults, children, currency }) {
  const useBodyHrId = process.env.HOTELRUNNER_USE_BODY_HR_ID === 'true';
  const debug = process.env.HOTELRUNNER_DEBUG_LOG_REQUEST === 'true';
  const rawPath = process.env.HOTELRUNNER_AVAILABILITY_RAW_PATH || "/api/v1/availability";
  const datePairs = parseDateKeyPairs(process.env.HOTELRUNNER_RAW_DATE_KEYS);
  const paramsBase = useBodyHrId ? {} : { hr_id: config.hotelrunner.id };
  const bodyBase = useBodyHrId ? { hr_id: config.hotelrunner.id } : {};
  const axiosCfg = { params: paramsBase };

  // We will try a few variants (GET with params; POST with body), and a few key pairs.
  const attempts = [];

  for (const [kStart, kEnd] of datePairs) {
    // Variant A: GET with params
    attempts.push({
      method: "get",
      path: rawPath,
      params: { ...paramsBase, [kStart]: check_in, [kEnd]: check_out, adults, children, currency },
      data: undefined
    });
    // Variant B: POST with body
    attempts.push({
      method: "post",
      path: rawPath,
      params: paramsBase,
      data: { ...bodyBase, [kStart]: check_in, [kEnd]: check_out, adults, children, currency }
    });
  }

  let lastErr;
  for (const a of attempts) {
    try {
      if (debug) console.log("[HR RAW try]", a.method, a.path, { params: a.params, data: a.data });
      const resp = await api.request({ method: a.method, url: a.path, params: a.params, data: a.data });
      return resp.data;
    } catch (e) {
      lastErr = e;
      if (e?.response?.status && e.response.status < 500) continue;
      else throw e;
    }
  }
  throw lastErr || new Error("All RAW availability attempts failed");
}

// Compute a simple aggregated view from raw availability payloads.
// This is intentionally defensive; adjust selectors to your tenant's shape.
export function computeInventoryFromRaw(raw, { check_in, check_out }) {
  // Heuristics: try a few common shapes
  // 1) raw = { dates: { "YYYY-MM-DD": { room_types: [{name, available}, ...] } } }
  // 2) raw = [{ date, rooms: [{type_name, available_count}, ...] }, ...]
  // 3) raw = { availability: [ { date, type, available }, ... ] }
  const out = {};
  const add = (d, name, n) => {
    if (!out[d]) out[d] = {};
    out[d][name] = (out[d][name] || 0) + (Number.isFinite(n) ? n : 0);
  };

  if (raw && typeof raw === "object") {
    if (raw.dates && typeof raw.dates === "object") {
      for (const [date, v] of Object.entries(raw.dates)) {
        const arr = v?.room_types || v?.rooms || [];
        for (const r of arr) {
          const name = r.name || r.type || r.type_name || "Room";
          const avail = Number(r.available ?? r.available_count ?? r.inventory ?? 0);
          add(date, name, avail);
        }
      }
      return out;
    }
    if (Array.isArray(raw)) {
      for (const day of raw) {
        const date = day.date || day.day || day.d || null;
        const rooms = day.rooms || day.room_types || [];
        if (date && rooms) {
          for (const r of rooms) {
            const name = r.name || r.type || r.type_name || "Room";
            const avail = Number(r.available ?? r.available_count ?? r.inventory ?? 0);
            add(date, name, avail);
          }
        }
      }
      return out;
    }
    if (Array.isArray(raw.availability)) {
      for (const it of raw.availability) {
        const date = it.date || it.day || it.d;
        const name = it.room_type || it.type || it.name || "Room";
        const avail = Number(it.available ?? it.available_count ?? it.inventory ?? 0);
        if (date) add(date, name, avail);
      }
      return out;
    }
  }
  // Fallback: return raw as-is if we can't interpret
  return { _raw: raw };
}

export async function searchAvailability(payload) {
  if (process.env.HOTELRUNNER_USE_RAW === 'true') {
    const raw = await getAvailabilityRaw(payload);
    return computeInventoryFromRaw(raw, payload);
  }

  if (mockMode) {
    return {
      mock: true,
      note: "HOTELRUNNER_MOCK_MODE enabled",
      request: payload,
      availability: {
        [payload.check_in]: { "Standard Room": 20, "Deluxe Room": 10 },
        [payload.check_out]: { "Standard Room": 20, "Deluxe Room": 10 }
      }
    };
  }

  if (!canPass()) {
    const err = new Error("Circuit open - fallback data");
    err.status = 503;
    throw err;
  }
  try {
    const { availabilityPath } = config.hotelrunner; const smart = process.env.HOTELRUNNER_SMART_STRATEGY === 'true';
    const altPaths = (process.env.HOTELRUNNER_ALT_PATHS || '').split(',').map(s=>s.trim()).filter(Boolean);
    const body = useBodyHrId ? { ...payload, hr_id: config.hotelrunner.id } : payload;
    if (debug) {
      // eslint-disable-next-line no-console
      console.log("[HR] POST", availabilityPath, { params: useBodyHrId ? {} : { hr_id: config.hotelrunner.id } , body });
    }
    let lastErr;
    const pathsToTry = [availabilityPath, ...altPaths];
    const variants = smart ? buildPayloadVariants(payload, config.hotelrunner.id, useBodyHrId) : [body];

    for (const path of pathsToTry) {
      for (const variant of variants) {
        try {
          if (debug) console.log("[HR try]", path, { params: useBodyHrId ? {} : { hr_id: config.hotelrunner.id }, body: variant });
          const resp = await api.post(path, variant);
          onSuccess();
          return resp.data;
        } catch (e) {
          lastErr = e;
          if (e?.response?.status && e.response.status < 500) {
            // continue trying other variants/paths only on 4xx
            continue;
          } else {
            // for network/5xx break out
            throw e;
          }
        }
      }
    }
    // if we reach here, all tries failed
    throw lastErr || new Error("All HotelRunner strategies exhausted");

  } catch (err) {
    // If a 404 happens, try an alternate base (if provided), or the same request w/ toggled hr_id position.
    if (err?.response?.status === 404) {
      try {
        const altBase = process.env.HOTELRUNNER_BASE_ALT;
        if (altBase) {
          const alt = axios.create({
            baseURL: altBase,
            timeout: 10000,
            headers: { Authorization: `Bearer ${config.hotelrunner.token}`, "Content-Type": "application/json" },
            params: useBodyHrId ? {} : { hr_id: config.hotelrunner.id },
          });
          const body = useBodyHrId ? { ...payload, hr_id: config.hotelrunner.id } : payload;
          if (debug) {
            // eslint-disable-next-line no-console
            console.log("[HR:ALT] POST", config.hotelrunner.availabilityPath, { params: useBodyHrId ? {} : { hr_id: config.hotelrunner.id }, body });
          }
          const resp2 = await alt.post(config.hotelrunner.availabilityPath, body);
          onSuccess();
          return resp2.data;
        }
      } catch (e2) {
        onFailure();
        e2.message = `[HR alt 404 try] ` + (e2.message || String(e2));
        throw e2;
      }
    }
    onFailure();
    // enrich error for better visibility
    const status = err?.response?.status;
    const data = err?.response?.data;
    const url = err?.config?.baseURL + err?.config?.url;
    const enriched = new Error(`HotelRunner error: ${status || "n/a"} at ${url} → ${JSON.stringify(data)}`);
    enriched.status = status || 502;
    throw enriched;
  }
}
