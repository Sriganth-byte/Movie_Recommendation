const BASE =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ||
  import.meta.env.REACT_APP_API_BASE_URL?.replace(/\/$/, "") ||
  "/api";

const REQUEST_TIMEOUT_MS = 15000;

function buildUrl(path, params = {}) {
  const url = new URL(`${BASE}${path}`);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, value);
    }
  });
  return url.toString();
}

async function fetchJSON(path, { params, ...options } = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  const externalSignal = options.signal;

  if (externalSignal) {
    if (externalSignal.aborted) controller.abort();
    externalSignal.addEventListener("abort", () => controller.abort(), { once: true });
  }

  try {
    const res = await fetch(buildUrl(path, params), {
      ...options,
      signal: controller.signal,
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`API ${res.status}: ${text || res.statusText}`);
    }
    return res.json();
  } finally {
    clearTimeout(timeout);
  }
}

export const getTopPicks = (options = {}) =>
  fetchJSON("/trending", { ...options, params: { limit: 6 } });

export const getMetadata = (options = {}) =>
  fetchJSON("/metadata", options);

export const getTrending = (offset = 0, limit = 10, options = {}) =>
  fetchJSON("/trending", { ...options, params: { offset, limit } });

export const getByGenre = (genre, offset = 0, limit = 10, options = {}) =>
  fetchJSON(`/genre/${encodeURIComponent(genre)}`, {
    ...options,
    params: { offset, limit },
  });

export const searchMovies = (q, offset = 0, limit = 10, options = {}) =>
  fetchJSON("/search", { ...options, params: { q, offset, limit } });

export const getSimilarMovies = (imdbId, offset = 0, limit = 5, options = {}) =>
  fetchJSON(`/movies/${encodeURIComponent(imdbId)}/similar`, {
    ...options,
    params: { offset, limit },
  });

export const getCredits = (imdbId, options = {}) =>
  fetchJSON(`/movies/${encodeURIComponent(imdbId)}/credits`, options);

export const getPersonalRecommendations = (
  payload = {},
  offset = 0,
  limit = 10,
  options = {}
) =>
  fetchJSON("/personal-recommend", {
    ...options,
    params: { offset, limit },
    method: "POST",
    headers: { "Content-Type": "application/json", ...options.headers },
    body: JSON.stringify(payload),
  });
