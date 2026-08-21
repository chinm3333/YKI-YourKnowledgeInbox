import { useState } from "react";
import { ingestItem } from "../api";
import { IconLink, IconNote, IconPlus } from "../icons.jsx";

export default function IngestForm({ onIngested }) {
  const [type, setType] = useState("note");
  const [content, setContent] = useState("");
  const [status, setStatus] = useState("idle");
  const [message, setMessage] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setStatus("loading");
    setMessage("");
    try {
      const item = await ingestItem(type, content);
      setStatus("ok");
      setMessage(`Indexed “${item.title}” · ${item.chunk_count} chunks`);
      setContent("");
      onIngested();
    } catch (error) {
      setStatus("error");
      setMessage(error.message);
    }
  }

  function onKeyDown(event) {
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
      event.currentTarget.form?.requestSubmit();
    }
  }

  return (
    <form className="card capture" onSubmit={handleSubmit}>
      <header className="card-head">
        <h2>Add source</h2>
        <p>Notes stay local. URLs are fetched on the server.</p>
      </header>

      <div className="segment" role="group" aria-label="Content type">
        <button type="button" className={type === "note" ? "on" : ""} onClick={() => setType("note")}>
          <IconNote /> Note
        </button>
        <button type="button" className={type === "url" ? "on" : ""} onClick={() => setType("url")}>
          <IconLink /> URL
        </button>
      </div>

      <label className="field">
        <span>{type === "url" ? "Page URL" : "Note"}</span>
        {type === "url" ? (
          <input
            type="url"
            required
            placeholder="https://docs.example.com/guide"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            onKeyDown={onKeyDown}
          />
        ) : (
          <textarea
            required
            rows={5}
            placeholder="Paste a decision, meeting note, or snippet…"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            onKeyDown={onKeyDown}
          />
        )}
        {type === "note" && <small>{content.trim().length} characters · Ctrl/⌘ + Enter</small>}
      </label>

      <button className="btn primary" type="submit" disabled={status === "loading" || !content.trim()}>
        <IconPlus />
        {status === "loading" ? "Indexing…" : "Add to inbox"}
      </button>

      {message && <p className={`hint ${status}`}>{message}</p>}
    </form>
  );
}
