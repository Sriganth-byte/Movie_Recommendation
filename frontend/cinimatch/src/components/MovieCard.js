import "../styles/movieCard.css";

const POSTER = "https://image.tmdb.org/t/p/w200";

export default function MovieCard({ movie, onClick }) {
  if (!movie?.poster_path) return null;

  return (
    <div
      className="movie-card"
      onClick={() => onClick?.(movie)}
    >
      <img src={`${POSTER}${movie.poster_path}`} alt={movie.title} />
      <p>{movie.title}</p>
    </div>
  );
}
