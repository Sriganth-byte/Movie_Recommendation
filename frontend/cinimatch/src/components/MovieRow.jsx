import { useCallback, useEffect, useRef, useState } from "react";
import MovieCard from "./MovieCard";
import { getByGenre, getTrending } from "../services/api";
import "../styles/movieRow.css";

const CARD_WIDTH = 160;
const LIMIT = 10;

export default function MovieRow({
  title,
  genre,
  fetchType,
  fetchMore,
  onSelect,
  autoLoad = true,
}) {
  const [movies, setMovies] = useState([]);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [hasMore, setHasMore] = useState(true);
  const rowRef = useRef(null);
  const requestRef = useRef(null);
  const initialLoadDone = useRef(false);

  const fetchPage = useCallback(
    (nextOffset, options = {}) => {
      if (fetchMore) return fetchMore(nextOffset, LIMIT, options);
      if (fetchType === "trending") return getTrending(nextOffset, LIMIT, options);
      return getByGenre(genre, nextOffset, LIMIT, options);
    },
    [fetchMore, fetchType, genre]
  );

  const loadMore = useCallback(async () => {
    if (loading || !hasMore) return;

    let controller;
    try {
      setLoading(true);
      setError("");
      requestRef.current?.abort();
      controller = new AbortController();
      requestRef.current = controller;

      const data = await fetchPage(offset, { signal: controller.signal });
      const nextMovies = Array.isArray(data) ? data : [];

      setMovies((prev) => {
        const seen = new Set(prev.map((m) => m.imdb_id || m.title));
        const fresh = nextMovies.filter((m) => !seen.has(m.imdb_id || m.title));
        return [...prev, ...fresh];
      });
      setOffset((prev) => prev + nextMovies.length);
      setHasMore(nextMovies.length === LIMIT);
    } catch (err) {
      if (err.name !== "AbortError") {
        console.error("MovieRow fetch failed:", err);
        setError("Could not load movies");
      }
    } finally {
      if (requestRef.current === controller && !controller.signal.aborted) {
        setLoading(false);
      }
    }
  }, [fetchPage, hasMore, loading, offset]);

  // Reset when the data source changes
  useEffect(() => {
    requestRef.current?.abort();
    setMovies([]);
    setOffset(0);
    setHasMore(true);
    setError("");
    initialLoadDone.current = false;
  }, [fetchPage]);

  // Trigger the first load once after reset, without depending on loading/movies state
  useEffect(() => {
    if (!autoLoad || initialLoadDone.current) return;
    initialLoadDone.current = true;
    loadMore();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fetchPage, autoLoad]);

  useEffect(() => () => requestRef.current?.abort(), []);

  function scroll(dir) {
    rowRef.current?.scrollBy({
      left: dir === "left" ? -CARD_WIDTH * 4 : CARD_WIDTH * 4,
      behavior: "smooth",
    });
  }

  const showArrows = movies.length > 5;

  return (
    <section className="row">
      <h2 className="row-title">{title}</h2>

      <div className="row-wrapper">
        {showArrows && (
          <button
            className="scroll-btn left"
            onClick={() => scroll("left")}
            aria-label={`Scroll ${title} left`}
          >
            &lsaquo;
          </button>
        )}

        <div ref={rowRef} className="row-list">
          {movies.map((m) => (
            <div key={m.imdb_id || m.title} className="movie-item">
              <MovieCard movie={m} onClick={onSelect} />
            </div>
          ))}

          {error && <div className="row-status">{error}</div>}

          {hasMore && (
            <button
              type="button"
              className={`more-card ${loading ? "disabled" : ""}`}
              onClick={loadMore}
              disabled={loading}
            >
              {loading ? "Loading..." : "+ More"}
            </button>
          )}
        </div>

        {showArrows && (
          <button
            className="scroll-btn right"
            onClick={() => scroll("right")}
            aria-label={`Scroll ${title} right`}
          >
            &rsaquo;
          </button>
        )}
      </div>
    </section>
  );
}
