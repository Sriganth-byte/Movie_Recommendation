import { useCallback } from "react";
import "../styles/movieCard.css";

const POSTER = "https://image.tmdb.org/t/p/w200";

export default function MovieCard({ movie, onClick }) {
  const handleClick = useCallback(() => onClick?.(movie), [movie, onClick]);

  if (!movie) return null;

  const poster = movie.poster_path
    ? `${POSTER}${movie.poster_path}`
    : "/logo192.png";

  return (
    <button
      type="button"
      className="movie-card"
      onClick={handleClick}
      aria-label={`View details for ${movie.title}`}
    >
      <img src={poster} alt="" loading="lazy" />
      <p>{movie.title}</p>
    </button>
  );
}
