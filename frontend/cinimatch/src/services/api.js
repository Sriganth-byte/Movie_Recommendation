// ================= BASE URL =================
const BASE = "https://cinimatch-backend.onrender.com";

// ================= FETCH HELPER =================
async function fetchJSON(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}

/* ================= BASIC ================= */

export const getTopPicks = () =>
  fetchJSON(`${BASE}/trending?limit=6`);

export const getTrending = (offset = 0, limit = 10) =>
  fetchJSON(`${BASE}/trending?offset=${offset}&limit=${limit}`);

export const getByGenre = (genre, offset = 0, limit = 10) =>
  fetchJSON(
    `${BASE}/genre/${encodeURIComponent(genre)}?offset=${offset}&limit=${limit}`
  );

/* ================= SEARCH ================= */

export const searchMovies = (q, offset = 0, limit = 10) =>
  fetchJSON(
    `${BASE}/search?q=${encodeURIComponent(q)}&offset=${offset}&limit=${limit}`
  );

/* ================= DETAILS (IMDB ID BASED) ================= */

export const getSimilarMovies = (imdbId, offset = 0, limit = 5) =>
  fetchJSON(
    `${BASE}/movies/${encodeURIComponent(imdbId)}/similar?offset=${offset}&limit=${limit}`
  );

export const getCredits = (imdbId) =>
  fetchJSON(
    `${BASE}/movies/${encodeURIComponent(imdbId)}/credits`
  );

/* ================= PERSONAL RECOMMEND ================= */

export const getPersonalRecommendations = (
  payload = {},
  offset = 0,
  limit = 10
) =>
  fetchJSON(
    `${BASE}/personal-recommend?offset=${offset}&limit=${limit}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );
