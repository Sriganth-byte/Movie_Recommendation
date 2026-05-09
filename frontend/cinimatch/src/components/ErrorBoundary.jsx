import { Component } from "react";

export default class ErrorBoundary extends Component {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    console.error("Application error:", error, info);
  }

  handleReload() {
    window.location.reload();
  }

  render() {
    if (this.state.hasError) {
      return (
        <main className="app-fallback">
          <h1>CiniMatch</h1>
          <p>Something went wrong while loading the experience.</p>
          <button type="button" onClick={this.handleReload}>
            Reload
          </button>
        </main>
      );
    }

    return this.props.children;
  }
}
