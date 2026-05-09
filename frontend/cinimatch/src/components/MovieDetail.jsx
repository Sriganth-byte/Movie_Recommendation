import { useEffect, useState } from "react";
import { getCredits, getSimilarMovies } from "../services/api";
import MovieCard from "./MovieCard";
import "../styles/movieDetail.css";

function normalizeGenres(genres) {
  if (!genres) return [];
  if (Array.isArray(genres)) return genres.slice(0, 4);
  if (typeof genres === "string") {
    return genres
      .split(",")
      .map((g) => g.trim())
      .filter(Boolean)
      .slice(0, 4);
  }
  return [];
}

export default function MovieDetails({ movie, onSelect }) {
  const [cast, setCast] = useState([]);
  const [similar, setSimilar] = useState([]);
  const [animate, setAnimate] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!movie?.imdb_id) return;

    const controller = new AbortController();
    let timer;

    async function loadDetails() {
      try {
        setLoading(true);
        setAnimate(false);
        setCast([]);
        setSimilar([]);

        const [credits, similarMovies] = await Promise.all([
          getCredits(movie.imdb_id, { signal: controller.signal }),
          getSimilarMovies(movie.imdb_id, 0, 7, { signal: controller.signal }),
        ]);

        setCast(Array.isArray(credits?.cast) ? credits.cast : []);
        setSimilar(Array.isArray(similarMovies) ? similarMovies.slice(0, 7) : []);
        timer = setTimeout(() => setAnimate(true), 100);
      } catch (err) {
        if (err.name !== "AbortError") {
          console.error("Movie details fetch failed:", err);
          setCast([]);
          setSimilar([]);
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadDetails();

    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [movie?.imdb_id]);

  if (!movie) return null;

  const genres = normalizeGenres(movie.genres);
  const rating = Number(movie.vote_average || movie.rating || 0).toFixed(1);
  const votes = Math.round(Number(movie.vote_count || movie.votes || 0)).toLocaleString();
  const popularity = Math.round(Number(movie.popularity || 0)).toLocaleString();

  return (
    <section className="details">
      <div className="details-layout">
        <div className="details-poster">
          <img
            src={
              movie.poster_path
                ? `https://image.tmdb.org/t/p/w500${movie.poster_path}`
                : "/logo512.png"
            }
            alt={movie.title}
          />
        </div>

        <div className="details-meta">
          <h1>{movie.title}</h1>

          <div className="header-stats">
            <span className="rating">Rating {rating}</span>
            <span>{votes} votes</span>
            <span>Popularity {popularity}</span>

            {genres.map((g) => (
              <span key={g} className="genre-chip">{g}</span>
            ))}
          </div>

          <p className="overview">
            {movie.overview || "No description available."}
          </p>

          {cast.length > 0 && (
            <div className="cast">
              <h3>Cast</h3>
              <div className="cast-list">
                {cast.slice(0, 6).map((c) => (
                  <span key={c.name}>{c.name}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {(loading || similar.length > 0) && (
        <div className="similar-section">
          <h3>More Like This</h3>

          {loading && <p className="details-status">Finding close matches...</p>}

          {similar.length > 0 && (
            <div className={`similar-row ${animate ? "show" : ""}`}>
              {similar.map((m, i) => (
                <div
                  key={m.imdb_id || m.title}
                  className="similar-item"
                  style={{ animationDelay: `${i * 80}ms` }}
                >
                  <MovieCard movie={m} onClick={onSelect} />
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
