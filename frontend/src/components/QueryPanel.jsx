import { useState } from "react";
import { queryInbox } from "../api";
import { IconSearch } from "../icons.jsx";

function AnswerText({ text, activeIndex, onCite }) {
  const parts = String(text).split(/(\[\d+\])/g);
  return (
    <p className="answer">
      {parts.map((part, i) => {
        const match = part.match(/^\[(\d+)\]$/);
        if (!match) {
          return <span key={i}>{part}</span>;
        }
        const n = Number(match[1]);
        return (
          <button
            key={i}
            type="button"
            className={activeIndex === n ? "cite on" : "cite"}
            onClick={() => onCite(n)}
          >
            {n}
          </button>
        );
      })}
    </p>
  );
}

export default function QueryPanel({ onHighlight, hasSources }) {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");
  const [activeIndex, setActiveIndex] = useState(null);

  async function handleSubmit(event) {
    event.preventDefault();
    setStatus("loading");
    setError("");
    setResult(null);
    setActiveIndex(null);
    try {
      const data = await queryInbox(question);
      setResult(data);
      setStatus("ok");
    } catch (err) {
      setStatus("error");
      setError(err.message);
    }
  }

  function selectSource(index) {
    setActiveIndex(index);
    const source = result?.sources[index - 1];
    if (source) onHighlight(source.item_id);
  }

  function onKeyDown(event) {
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
      event.currentTarget.form?.requestSubmit();
    }
  }

  return (
    <section className="card ask">
      <header className="card-head">
        <h2>Ask</h2>
        <p>Answers are grounded in retrieved chunks. Click a citation to inspect the source.</p>
      </header>

      <form className="composer" onSubmit={handleSubmit}>
        <label className="field">
          <span>Question</span>
          <textarea
            required
            minLength={3}
            rows={3}
            placeholder={hasSources ? "Ask something you saved…" : "Add a source first, then ask."}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={onKeyDown}
          />
        </label>
        <div className="composer-bar">
          <small>Ctrl/⌘ + Enter</small>
          <button className="btn primary" type="submit" disabled={status === "loading" || question.trim().length < 3}>
            <IconSearch />
            {status === "loading" ? "Retrieving…" : "Ask"}
          </button>
        </div>
      </form>

      {status === "loading" && (
        <div className="progress" role="status">
          <span />
          Searching embeddings, then generating an answer
        </div>
      )}

      {error && <p className="hint error">{error}</p>}

      {!result && status !== "loading" && (
        <div className="empty">
          <div className="empty-art" aria-hidden="true" />
          <p>Your answer will appear here</p>
          <span>Retrieval uses MiniLM locally. Generation uses Groq, with citations.</span>
        </div>
      )}

      {result && (
        <div className="result">
          <div className="result-label">Answer</div>
          <AnswerText text={result.answer} activeIndex={activeIndex} onCite={selectSource} />

          <div className="result-label">Sources</div>
          {result.sources.length === 0 && <p className="hint">No matching chunks for this question.</p>}
          <ul className="sources">
            {result.sources.map((source, index) => (
              <li key={`${source.item_id}-${index}`}>
                <button
                  type="button"
                  className={activeIndex === index + 1 ? "source on" : "source"}
                  onClick={() => selectSource(index + 1)}
                >
                  <div className="source-top">
                    <span className="cite on static">{index + 1}</span>
                    <span className={`pill ${source.type}`}>{source.type}</span>
                    <span className="score">{Math.round(source.score * 100)}% match</span>
                  </div>
                  <strong>{source.title}</strong>
                  {source.source && (
                    <a
                      className="source-link"
                      href={source.source}
                      target="_blank"
                      rel="noreferrer"
                      onClick={(event) => event.stopPropagation()}
                    >
                      {source.source.replace(/^https?:\/\//, "")}
                    </a>
                  )}
                  <p>{source.snippet}</p>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
