export default function HomePage() {
  return (
    <main
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        padding: "2rem",
        textAlign: "center",
      }}
    >
      <div
        style={{
          background: "var(--bg-secondary)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "var(--radius-lg)",
          padding: "3rem",
          maxWidth: "600px",
          boxShadow: "0 8px 32px rgba(0, 0, 0, 0.4)",
        }}
      >
        <div
          style={{
            display: "inline-block",
            padding: "0.25rem 0.75rem",
            borderRadius: "var(--radius-sm)",
            background: "var(--accent-glow)",
            color: "var(--accent-primary)",
            fontSize: "0.875rem",
            fontWeight: 600,
            marginBottom: "1rem",
          }}
        >
          Track 02 — BFSI Defense
        </div>
        <h1
          style={{
            fontSize: "2rem",
            fontWeight: 700,
            marginBottom: "1rem",
            color: "var(--text-primary)",
          }}
        >
          AI Risk Manager
        </h1>
        <p
          style={{
            color: "var(--text-secondary)",
            lineHeight: 1.6,
            marginBottom: "2rem",
          }}
        >
          Real-time detection, scoring, and auto-responder system for fraud,
          returns, and chargeback loss prevention.
        </p>
        <div
          style={{
            display: "flex",
            gap: "1rem",
            justifyContent: "center",
          }}
        >
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            style={{
              display: "inline-flex",
              alignItems: "center",
              padding: "0.75rem 1.5rem",
              background: "var(--accent-primary)",
              color: "#ffffff",
              borderRadius: "var(--radius-md)",
              fontWeight: 500,
              textDecoration: "none",
            }}
          >
            Backend API Docs
          </a>
        </div>
      </div>
    </main>
  );
}
