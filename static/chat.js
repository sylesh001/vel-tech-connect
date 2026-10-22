document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("chat-form");
  if (!form) return;
  const input = document.getElementById("chat-input");
  const messages = document.getElementById("chat-messages");
  const sendButton = form.querySelector("button");
  const suggestions = document.querySelectorAll("[data-question]");
  let sending = false;

  function addMessage(text, kind) {
    const wrap = document.createElement("div");
    wrap.className = `message ${kind === "user" ? "user-message" : "bot-message"}`;
    if (kind === "typing") {
      wrap.classList.add("typing-message");
      wrap.setAttribute("role", "status");
      wrap.setAttribute("aria-label", "Assistant is preparing a response");
    }
    const avatar = document.createElement("span");
    avatar.className = "message-avatar";
    avatar.setAttribute("aria-hidden", "true");
    avatar.textContent = kind === "user" ? "You" : "✦";
    const body = document.createElement("div");
    const label = document.createElement("strong");
    label.textContent = kind === "user" ? "You" : "Vel Tech Assistant";
    const p = document.createElement("p");
    if (kind === "typing") {
      p.className = "typing-indicator";
      p.textContent = "Finding an answer…";
    } else {
      p.textContent = text;
    }
    body.append(label, p);
    wrap.append(avatar, body);
    messages.appendChild(wrap);
    messages.scrollTop = messages.scrollHeight;
    return wrap;
  }

  async function send(text) {
    const question = (text || input.value).trim();
    if (!question || sending) return;
    sending = true;
    addMessage(question, "user");
    input.value = "";
    input.disabled = true;
    sendButton.disabled = true;
    suggestions.forEach((button) => { button.disabled = true; });
    const typingMessage = addMessage("", "typing");
    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message: question})
      });
      const data = await response.json();
      typingMessage.remove();
      if (!response.ok) {
        addMessage(data.answer || "I couldn’t process that question. Please try again.", "bot");
      } else {
        addMessage(data.answer || "I couldn’t find a reliable answer. Try asking about courses, admissions, fees or campus services.", "bot");
      }
    } catch (_error) {
      typingMessage.remove();
      addMessage("There was a connection error. Please try again.", "bot");
    } finally {
      sending = false;
      input.disabled = false;
      sendButton.disabled = false;
      suggestions.forEach((button) => { button.disabled = false; });
      input.focus();
    }
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    send();
  });
  document.querySelectorAll("[data-question]").forEach((button) => {
    button.addEventListener("click", () => send(button.dataset.question));
  });
});
