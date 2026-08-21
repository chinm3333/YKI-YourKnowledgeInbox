import { useState } from "react";
import { deleteItem } from "../api";
import { IconTrash, relativeTime } from "../icons.jsx";

export default function ItemList({ items, selectedId, onSelect, onDeleted, onError, loading, }) {
  const [pendingId, setPendingId] = useState(null);
  const [busyId, setBusyId] = useState(null);

  async function confirmDelete(id) {
    setBusyId(id);
    try {
      await deleteItem(id);
      onDeleted(id);
      setPendingId(null);
    } catch (error) {
      onError?.(error.message);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section className="card inbox">
      <header className="card-head row">
        <div>
          <h2>Inbox</h2>
          <p>{loading ? "Loading sources" : `${items.length} indexed source${items.length === 1 ? "" : "s"}`}</p>
        </div>
      </header>

      {loading && (
        <div className="skeletons" aria-hidden="true">
          <div className="skel" />
          <div className="skel" />
          <div className="skel" />
        </div>
      )}

      {!loading && items.length === 0 && (
        <div className="empty compact">
          <p>No sources yet</p>
          <span>Add a note or URL to start retrieval.</span>
        </div>
      )}

      <ul className="feed">
        {items.map((item) => {
          const selected = item.id === selectedId;
          const pending = pendingId === item.id;
          return (
            <li key={item.id} className={selected ? "row selected" : "row"}>
              <button type="button" className="row-main" onClick={() => onSelect(item.id)}>
                <div className="row-top">
                  <span className={`pill ${item.type}`}>{item.type}</span>
                  <time dateTime={item.created_at}>{relativeTime(item.created_at)}</time>
                </div>
                <strong>{item.title}</strong>
                <p>{item.preview}</p>
              </button>
              {pending ? (
                <div className="confirm">
                  <button type="button" className="text-btn danger" disabled={busyId === item.id} onClick={() => confirmDelete(item.id)}>
                    {busyId === item.id ? "Removing…" : "Confirm"}
                  </button>
                  <button type="button" className="text-btn" onClick={() => setPendingId(null)}>
                    Cancel
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  className="icon-btn"
                  aria-label={`Delete ${item.title}`}
                  onClick={() => setPendingId(item.id)}
                >
                  <IconTrash />
                </button>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
