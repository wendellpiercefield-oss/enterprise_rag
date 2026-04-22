let authToken = localStorage.getItem("token") || "";
let currentUser = null;
let currentCollectionId = null;

// -------------------------
// Helpers
// -------------------------
function escapeHtml(str) {
  return String(str || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function setStatus(message) {
  const el = document.getElementById("uploadStatus");
  if (el) el.textContent = message || "";
}

function setModeBadge(message) {
  const el = document.getElementById("modeBadge");
  if (el) el.textContent = message || "";
}

function setUserBadge(message) {
  const el = document.getElementById("userBadge");
  if (el) el.textContent = message || "";
}

function showLogin() {
  const loginPanel = document.getElementById("loginPanel");
  const appPanel = document.getElementById("appPanel");

  if (loginPanel) loginPanel.style.display = "block";
  if (appPanel) appPanel.style.display = "none";
}

function showApp() {
  const loginPanel = document.getElementById("loginPanel");
  const appPanel = document.getElementById("appPanel");

  if (loginPanel) loginPanel.style.display = "none";
  if (appPanel) appPanel.style.display = "block";
}

async function apiFetch(url, options = {}) {
  const headers = { ...(options.headers || {}) };

  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }

  const response = await fetch(url, {
    ...options,
    headers
  });

  if (response.status === 401) {
    logout();
    throw new Error("Unauthorized");
  }

  return response;
}

// -------------------------
// Auth
// -------------------------
async function login() {
  const email = document.getElementById("email")?.value.trim();
  const password = document.getElementById("password")?.value || "";

  if (!email || !password) {
    alert("Enter email and password");
    return;
  }

  try {
    const response = await fetch("http://localhost:8000/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        email,
        password
      })
    });

    if (!response.ok) {
      const errText = await response.text();
      console.error(errText);
      throw new Error("Login failed");
    }

    const data = await response.json();
    authToken = data.access_token || "";

    if (!authToken) {
      throw new Error("No token returned");
    }

    localStorage.setItem("token", authToken);

    await loadMe();
    await loadCollections();

    showApp();
    setModeBadge("");
  } catch (err) {
    console.error(err);
    alert("Login failed");
  }
}

async function loadMe() {
  const response = await apiFetch("http://localhost:8000/auth/me");

  if (!response.ok) {
    throw new Error("Could not load current user");
  }

  currentUser = await response.json();
  setUserBadge(currentUser?.email || "");
}

function logout() {
  authToken = "";
  currentUser = null;
  currentCollectionId = null;

  localStorage.removeItem("token");

  const chatWindow = document.getElementById("chatWindow");
  const sources = document.getElementById("sources");
  const collectionSelect = document.getElementById("collectionSelect");
  const doclist = document.getElementById("doclist");

  if (chatWindow) chatWindow.innerHTML = "";
  if (sources) sources.innerHTML = "";
  if (collectionSelect) collectionSelect.innerHTML = "";
  if (doclist) doclist.innerHTML = "Manuals will appear here";

  setUserBadge("");
  setModeBadge("");
  setStatus("");

  showLogin();
}

// -------------------------
// Collections
// -------------------------
async function loadCollections() {
  const response = await apiFetch("http://localhost:8000/collections/");

  if (!response.ok) {
    const errText = await response.text();
    console.error(errText);
    throw new Error("Could not load collections");
  }

  const collections = await response.json();
  const select = document.getElementById("collectionSelect");
  const doclist = document.getElementById("doclist");

  if (!select) return;

  select.innerHTML = "";

  if (!collections || collections.length === 0) {
    currentCollectionId = null;

    const option = document.createElement("option");
    option.value = "";
    option.textContent = "No collections available";
    select.appendChild(option);

    if (doclist) {
      doclist.innerHTML = "No collections found. Create one in the backend first.";
    }

    return;
  }

  for (const c of collections) {
    const option = document.createElement("option");
    option.value = c.id;
    option.textContent = c.name;
    select.appendChild(option);
  }

  currentCollectionId = Number(collections[0].id);
  select.value = String(currentCollectionId);

  if (doclist) {
    doclist.innerHTML = collections
      .map(c => `<div>${escapeHtml(c.name)} (ID ${c.id})</div>`)
      .join("");
  }
}

function onCollectionChange() {
  const select = document.getElementById("collectionSelect");
  if (!select || !select.value) {
    currentCollectionId = null;
    return;
  }

  currentCollectionId = Number(select.value);
}

// -------------------------
// Chat UI helpers
// -------------------------
function addUserMessage(content) {
  const chat = document.getElementById("chatWindow");
  const div = document.createElement("div");
  div.className = "message user";
  div.textContent = content;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

function addAssistantMessage(initialText = "") {
  const chat = document.getElementById("chatWindow");
  const div = document.createElement("div");
  div.className = "message bot";
  div.innerHTML = marked.parse(initialText || "");
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
  return div;
}

function updateAssistantMessage(el, content) {
  el.innerHTML = marked.parse(content || "");
  const chat = document.getElementById("chatWindow");
  chat.scrollTop = chat.scrollHeight;
}

// -------------------------
// Chat
// -------------------------
async function ask() {
  const input = document.getElementById("question");
  const question = input?.value.trim();

  if (!question) return;

  addUserMessage(question);
  input.value = "";

  const assistantEl = addAssistantMessage("Thinking...");
  let fullText = "";

  try {
    const response = await apiFetch("http://localhost:8000/chat/stream", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        query: question
      })
    });

    if (!response.ok || !response.body) {
      const errText = await response.text();
      console.error(errText);
      updateAssistantMessage(assistantEl, "Failed to get response.");
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      const events = buffer.split("\n\n");
      buffer = events.pop() || "";

      for (const evt of events) {
        const line = evt
          .split("\n")
          .find(x => x.startsWith("data: "));

        if (!line) continue;

        let payload;
        try {
          payload = JSON.parse(line.slice(6));
        } catch (e) {
          console.error("Bad SSE payload:", e, line);
          continue;
        }

        if (payload.token) {
          if (fullText === "" || fullText === "Thinking...") {
            fullText = payload.token;
          } else {
            fullText += payload.token;
          }
          updateAssistantMessage(assistantEl, fullText);
        }

        if (payload.done) {
          if (!fullText) {
            updateAssistantMessage(assistantEl, "No answer returned.");
          }

          renderSources(payload.sources || [], question);

          if (payload.mode === "rag") {
            setModeBadge("Using manuals");
          } else if (payload.mode === "general") {
            setModeBadge("General knowledge fallback");
          } else {
            setModeBadge("");
          }
        }
      }
    }
  } catch (err) {
    console.error(err);
    updateAssistantMessage(assistantEl, "Error getting response.");
  }
}

// -------------------------
// Sources
// -------------------------
function renderSources(sources, question) {
  const container = document.getElementById("sources");
  if (!container) return;

  container.innerHTML = "";

  if (!sources || sources.length === 0) {
    container.innerHTML = "<i>No manual sources used</i>";
    return;
  }

  const keywords = question
    .toLowerCase()
    .replace(/[^\w\s]/g, "")
    .split(" ")
    .filter(w => w.length > 3);

  for (const s of sources) {
    const div = document.createElement("div");
    div.className = "source";

    const filename = s.filename || "Document";
    const chunk = s.chunk_index ?? "?";
    const sourceType = s.source || "";
    let content = s.content || "";

    content = escapeHtml(content);

    for (const k of keywords) {
      const regex = new RegExp(`(${k})`, "gi");
      content = content.replace(regex, "<mark>$1</mark>");
    }

    const preview = content.substring(0, 260);

    div.innerHTML = `
      <b>${escapeHtml(filename)} (chunk ${chunk})</b>
      <span style="color:#888">[${escapeHtml(sourceType)}]</span><br>
      <span class="preview">${preview}...</span>
      <div class="full" style="display:none; margin-top:8px;">${content}</div>
    `;

    div.onclick = function () {
      const full = div.querySelector(".full");
      full.style.display =
        full.style.display === "block" ? "none" : "block";
    };

    container.appendChild(div);
  }
}

// -------------------------
// Upload
// -------------------------
async function upload() {
  const fileInput = document.getElementById("fileUpload");

  if (!currentCollectionId) {
    alert("Select a collection first");
    return;
  }

  if (!fileInput || !fileInput.files.length) {
    alert("Select a file first");
    return;
  }

  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append("file", file);

  try {
    setStatus("Uploading...");

    const response = await apiFetch(
      `http://localhost:8000/documents/upload/${currentCollectionId}`,
      {
        method: "POST",
        body: formData
      }
    );

    if (!response.ok) {
      const errText = await response.text();
      console.error(errText);
      throw new Error("Upload failed");
    }

    const result = await response.json();

    setStatus(`Uploaded: ${result.filename} (${result.status})`);
    fileInput.value = "";
  } catch (err) {
    console.error(err);
    setStatus("Upload failed");
    alert("Upload error");
  }
}

// -------------------------
// Startup
// -------------------------
window.addEventListener("DOMContentLoaded", async function () {
  const questionInput = document.getElementById("question");
  if (questionInput) {
    questionInput.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        ask();
      }
    });
  }

  if (authToken) {
    try {
      await loadMe();
      await loadCollections();
      showApp();
    } catch (err) {
      console.error(err);
      logout();
    }
  } else {
    showLogin();
  }
});
