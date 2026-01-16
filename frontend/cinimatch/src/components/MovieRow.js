import { useEffect, useRef, useState } from "react";
import MovieCard from "./MovieCard";
import { getTrending, getByGenre } from "../services/api";
import "../styles/movieRow.css";

const CARD_WIDTH = 160;

export default function MovieRow({
  title,
  genre,
  fetchType,
  fetchMore,
  onSelect,
  autoLoad = true, // ✅ NEW
}) {
  const [movies, setMovies] = useState([]);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);

  const LIMIT = 10;
  const rowRef = useRef(null);

  /* ---------- INITIAL LOAD ---------- */
  useEffect(() => {
    if (!autoLoad) return;
    loadMore();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* ---------- DATA FETCH ---------- */
  async function loadMore() {
    if (loading) return;

    try {
      setLoading(true);
      let data = [];

      if (fetchMore) {
        data = await fetchMore(offset, LIMIT);
      } else if (fetchType === "trending") {
        data = await getTrending(offset, LIMIT);
      } else {
        data = await getByGenre(genre, offset, LIMIT);
      }

      if (Array.isArray(data) && data.length > 0) {
        setMovies((prev) => [...prev, ...data]);
        setOffset((prev) => prev + LIMIT);
      }
    } catch (err) {
      console.error("MovieRow fetch failed:", err);
    } finally {
      setLoading(false);
    }
  }

  /* ---------- SCROLL ---------- */
  function scroll(dir) {
    if (!rowRef.current) return;

    rowRef.current.scrollBy({
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
          <button className="scroll-btn left" onClick={() => scroll("left")}>
            ‹
          </button>
        )}

        <div ref={rowRef} className="row-list">
          {movies.map((m) => (
            <div
              key={m.imdb_id}   // ✅ STABLE UNIQUE KEY
              className="movie-item"
            >
              <MovieCard
                movie={m}
                onClick={onSelect}
              />
            </div>
          ))}


          <div
            className={`more-card ${loading ? "disabled" : ""}`}
            onClick={loadMore}
          >
            {loading ? "Loading…" : "+ More"}
          </div>
        </div>

        {showArrows && (
          <button className="scroll-btn right" onClick={() => scroll("right")}>
            ›
          </button>
        )}
      </div>
    </section>
  );
}
