import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import App from "./App";
import * as api from "./services/api";

vi.mock("./services/api", () => ({
  getTopPicks: vi.fn(),
  getMetadata: vi.fn(),
  getTrending: vi.fn(),
  getByGenre: vi.fn(),
  getCredits: vi.fn(),
  getSimilarMovies: vi.fn(),
  searchMovies: vi.fn(),
  getPersonalRecommendations: vi.fn(),
}));

test("renders the CiniMatch shell", async () => {
  api.getTopPicks.mockResolvedValue([
    {
      imdb_id: "tt0816692",
      title: "Interstellar",
      genres: "Adventure,Drama,Sci-Fi",
      overview: "A team travels through a wormhole.",
      poster_path: "",
      backdrop_path: "",
      vote_average: 8.4,
      vote_count: 1000,
      popularity: 100,
    },
  ]);
  api.getTrending.mockResolvedValue([]);
  api.getMetadata.mockResolvedValue({
    genres: ["Action", "Drama", "Comedy", "Mystery", "Sci-Fi", "Thriller"],
    moods: ["Fast", "Dark"],
    yearMin: 1900,
    yearMax: 2026,
    movieCount: 1,
    datasetSha256: "a".repeat(64),
  });
  api.getByGenre.mockResolvedValue([]);
  api.getCredits.mockResolvedValue({ cast: [] });
  api.getSimilarMovies.mockResolvedValue([]);
  api.searchMovies.mockResolvedValue([]);
  api.getPersonalRecommendations.mockResolvedValue([]);

  render(<App />);

  expect(await screen.findAllByText("Interstellar")).toHaveLength(2);
  expect(screen.getByText("CiniMatch")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /personal movie recommendations/i })).toBeInTheDocument();
});

test("uses metadata in the recommendation modal", async () => {
  api.getTopPicks.mockResolvedValue([]);
  api.getTrending.mockResolvedValue([]);
  api.getMetadata.mockResolvedValue({
    genres: ["Mystery", "Sci-Fi"],
    moods: ["Fast"],
    yearMin: 1950,
    yearMax: 2026,
    movieCount: 2,
    datasetSha256: "b".repeat(64),
  });
  api.getByGenre.mockResolvedValue([]);
  api.getCredits.mockResolvedValue({ cast: [] });
  api.getSimilarMovies.mockResolvedValue([]);
  api.searchMovies.mockResolvedValue([]);
  api.getPersonalRecommendations.mockResolvedValue([]);

  render(<App />);

  await userEvent.click(
    await screen.findByRole("button", { name: /personal movie recommendations/i })
  );

  expect(screen.getByRole("button", { name: "Mystery" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Sci-Fi" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Fast" })).toBeInTheDocument();
});
