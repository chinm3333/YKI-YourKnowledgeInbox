const BASE = import.meta.env.VITE_API_URL || "";

async function request(path, options = {}) {
  const response = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = data.detail || data.error || `Request failed (${response.status})`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  return data;
}

export function ingestItem(type, content) {
  return request("/ingest", {
    method: "POST",
    body: JSON.stringify({ type, content }),
  });
}

export function listItems() {
  return request("/items");
}

export function deleteItem(id) {
  return request(`/items/${id}`, { method: "DELETE" });
}

export function queryInbox(question, topK = 5) {
  return request("/query", {
    method: "POST",
    body: JSON.stringify({ question, top_k: topK }),
  });
}
