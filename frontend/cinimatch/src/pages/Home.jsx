import { useCallback, useEffect, useState } from "react";

import Navbar from "../components/Navbar";
import HallOfFame from "../components/HallOfFame";
import MovieDetails from "../components/MovieDetail";
import MovieRow from "../components/MovieRow";
import PersonalRecoModal from "../components/PersonalRecoModal";

import {
  getTopPicks,
  getMetadata,
  getPersonalRecommendations,
} from "../services/api";

const FALLBACK_GENRES = ["Action", "Drama", "Comedy", "Horror", "Romance"];

export default function Home() {
  const [topPicks, setTopPicks] = useState([]);
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [homeError, setHomeError] = useState("");
  const [metadata, setMetadata] = useState(null);

  const [openReco, setOpenReco] = useState(false);
  const [recoInput, setRecoInput] = useState(null);

  /* ================= INITIAL LOAD ================= */
  useEffect(() => {
    const controller = new AbortController();

    Promise.all([
      getTopPicks({ signal: controller.signal }),
      getMetadata({ signal: controller.signal }),
    ])
      .then((data) => {
        const [picks, catalogMetadata] = data;
        setTopPicks(picks || []);
        setSelectedMovie(picks?.[0] || null);
        setMetadata(catalogMetadata || null);
      })
      .catch((err) => {
        if (err.name !== "AbortError") {
          console.error("Initial load failed:", err);
          setHomeError("Could not load movie picks. Please check the backend.");
        }
      });

    return () => controller.abort();
  }, []);

  const fetchPersonalRecommendations = useCallback(
    (offset, limit, options) =>
      getPersonalRecommendations(recoInput, offset, limit, options),
    [recoInput]
  );

  /* ================= MOVIE SELECTION ================= */
  function handleSelect(movie) {
    if (!movie) return;

    // reset personal recommendations when user manually selects
    setRecoInput(null);
    setSelectedMovie(movie);
  }

  /* ================= OPEN RECO MODAL ================= */
  function openRecommendationModal() {
    // clear previous recommendation results
    setRecoInput(null);
    setOpenReco(true);
  }

  return (
    <>
      <Navbar
        onSelect={handleSelect}
        onOpenReco={openRecommendationModal}
      />

      <HallOfFame
        movies={topPicks}
        onSelect={handleSelect}
      />

      {homeError && <p className="home-error">{homeError}</p>}

      <MovieDetails
        movie={selectedMovie}
        onSelect={handleSelect}
      />


      {/* ================= PERSONAL RECOMMENDATIONS ================= */}
      {recoInput && (
        <MovieRow
          title="Recommended For You"
          autoLoad={true}
          fetchMore={fetchPersonalRecommendations}
          onSelect={handleSelect}
        />
      )}

      {/* ================= TRENDING ================= */}
      <MovieRow
        title="Trending"
        fetchType="trending"
        onSelect={handleSelect}
      />

      {/* ================= GENRES ================= */}
      {(metadata?.genres?.length ? metadata.genres.slice(0, 5) : FALLBACK_GENRES).map((g) => (
        <MovieRow
          key={g}
          title={g}
          genre={g}
          fetchType="genre"
          onSelect={handleSelect}
        />
      ))}

      {/* ================= MODAL ================= */}
      <PersonalRecoModal
        open={openReco}
        metadata={metadata}
        onClose={() => setOpenReco(false)}
        onSubmit={(data) => {
          setRecoInput(data);
          setOpenReco(false);
        }}
      />
    </>
  );
}
