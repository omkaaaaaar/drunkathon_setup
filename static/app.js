(() => {
  const micButton = document.getElementById("mic-button");
  const micLabel = document.getElementById("mic-button-label");
  const statusText = document.getElementById("status-text");
  const hintText = document.getElementById("hint-text");
  const languageSelect = document.getElementById("language-select");
  const conversation = document.getElementById("conversation");
  const emptyConversation = document.getElementById("empty-conversation");
  const replyAudio = document.getElementById("reply-audio");
  const card = document.querySelector(".voice-card");
  const connectionLabel = document.getElementById("connection-label");
  const resetButton = document.getElementById("reset-button");

  let recorder = null;
  let stream = null;
  let chunks = [];
  let recording = false;
  let busy = false;

  function setStatus(message, state = "") {
    statusText.textContent = message;
    card.classList.remove("is-recording", "is-processing", "is-speaking");
    if (state) card.classList.add(`is-${state}`);
  }

  function setBusy(value) {
    busy = value;
    micButton.disabled = value;
    if (value) {
      micLabel.textContent = "Working on your answer…";
      micButton.setAttribute("aria-label", "Processing your request");
    } else if (!recording) {
      micLabel.textContent = "Tap to speak";
      micButton.setAttribute("aria-label", "Start recording");
    }
  }

  function removeEmptyState() {
    if (emptyConversation) emptyConversation.remove();
  }

  function addMessage(role, label, text, audioUrl = null) {
    removeEmptyState();
    const bubble = document.createElement("div");
    bubble.className = `message ${role}`;
    const title = document.createElement("span");
    title.className = "message-label";
    title.textContent = label;
    const body = document.createElement("div");
    body.textContent = text;
    bubble.append(title, body);
    if (audioUrl && role === "assistant") {
      const play = document.createElement("button");
      play.type = "button";
      play.className = "reply-play";
      play.textContent = "▶ Play spoken answer";
      play.addEventListener("click", async () => {
        replyAudio.src = audioUrl;
        replyAudio.hidden = false;
        try {
          await replyAudio.play();
          setStatus("JanSathi is speaking…", "speaking");
        } catch (_) {
          setStatus("Tap the audio player to hear the answer.");
        }
      });
      bubble.appendChild(play);
    }
    conversation.appendChild(bubble);
    conversation.scrollTop = conversation.scrollHeight;
  }

  function supportedMimeType() {
    if (!window.MediaRecorder) return "";
    const choices = [
      "audio/webm;codecs=opus",
      "audio/webm",
      "audio/mp4",
      "audio/ogg;codecs=opus"
    ];
    return choices.find(type => MediaRecorder.isTypeSupported(type)) || "";
  }

  function extensionForMime(mime) {
    if (mime.includes("webm")) return "webm";
    if (mime.includes("ogg")) return "ogg";
    if (mime.includes("mp4")) return "mp4";
    return "webm";
  }

  async function startRecording() {
    if (busy || recording) return;
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      setStatus("This browser doesn't support microphone recording. Try a recent version of Chrome, Edge, or Safari.");
      return;
    }
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true }
      });
      chunks = [];
      const mimeType = supportedMimeType();
      recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      recorder.addEventListener("dataavailable", event => {
        if (event.data && event.data.size > 0) chunks.push(event.data);
      });
      recorder.addEventListener("stop", handleRecordingStop, { once: true });
      recorder.start();
      recording = true;
      micButton.classList.add("recording");
      micLabel.textContent = "Tap to send recording";
      micButton.setAttribute("aria-label", "Stop and send recording");
      setStatus("Listening… speak naturally, then tap to send.", "recording");
      hintText.textContent = "Keep your question short for a faster response.";
    } catch (error) {
      setStatus(error.name === "NotAllowedError"
        ? "Microphone permission was blocked. Allow microphone access in your browser settings."
        : "Couldn't access the microphone. Check that it is connected and try again.");
    }
  }

  function stopRecording() {
    if (!recording || !recorder) return;
    recording = false;
    micButton.classList.remove("recording");
    micButton.disabled = true;
    micLabel.textContent = "Sending your voice…";
    micButton.setAttribute("aria-label", "Sending recording");
    if (recorder.state !== "inactive") recorder.stop();
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      stream = null;
    }
    setStatus("Sending your question…", "processing");
  }

  async function handleRecordingStop() {
    const mimeType = recorder?.mimeType || chunks[0]?.type || "audio/webm";
    const blob = new Blob(chunks, { type: mimeType });
    chunks = [];
    if (blob.size < 500) {
      setBusy(false);
      micButton.disabled = false;
      setStatus("That recording was too short. Please try again.");
      return;
    }
    setBusy(true);
    const form = new FormData();
    form.append("audio", blob, `recording.${extensionForMime(mimeType)}`);
    form.append("language", languageSelect.value);

    try {
      setStatus("Understanding your words…", "processing");
      const response = await fetch("/api/voice", { method: "POST", body: form });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.error || `Request failed (${response.status}).`);

      addMessage("user", "YOU SAID", data.transcript);
      addMessage("assistant", "JANSATHI", data.reply, data.audio_url);
      replyAudio.src = data.audio_url;
      replyAudio.hidden = false;
      replyAudio.onplay = () => setStatus("JanSathi is speaking…", "speaking");
      replyAudio.onended = () => setStatus("Your turn. Ask me another question.");
      setStatus("Here's your answer. Playing it now…", "speaking");
      try {
        await replyAudio.play();
      } catch (_) {
        setStatus("Your answer is ready. Tap “Play spoken answer” to hear it.");
      }
      hintText.textContent = "You can ask a follow-up without starting over.";
    } catch (error) {
      setStatus(error.message || "Something went wrong. Please try again.");
      hintText.textContent = "Check your connection and try a short recording.";
    } finally {
      setBusy(false);
      micButton.disabled = false;
      micButton.classList.remove("recording");
      recording = false;
    }
  }

  micButton.addEventListener("click", () => {
    if (busy) return;
    if (recording) stopRecording();
    else startRecording();
  });

  resetButton.addEventListener("click", async () => {
    if (busy || recording) return;
    try {
      await fetch("/api/reset", { method: "POST" });
      conversation.replaceChildren();
      const empty = document.createElement("div");
      empty.className = "empty-conversation";
      empty.textContent = "Your conversation will appear here.";
      conversation.appendChild(empty);
      replyAudio.pause();
      replyAudio.removeAttribute("src");
      replyAudio.hidden = true;
      setStatus("New conversation ready. What would you like to know?");
      hintText.textContent = "For example: “मी महाराष्ट्रातील शेतकरी आहे.”";
    } catch (_) {
      setStatus("Couldn't reset the conversation. Refresh the page to try again.");
    }
  });

  replyAudio.addEventListener("play", () => {
    if (!replyAudio.hidden) setStatus("JanSathi is speaking…", "speaking");
  });
  replyAudio.addEventListener("ended", () => {
    setStatus("Your turn. Ask me another question.");
  });

  fetch("/api/health")
    .then(response => response.json())
    .then(data => {
      if (data.mock_mode) {
        connectionLabel.textContent = "Setup needed";
        setStatus("Voice APIs are in mock mode. Set MOCK_MODE=false in .env and restart the server.");
      } else if (!data.stt_model_configured || !data.tts_model_configured) {
        connectionLabel.textContent = "Setup needed";
        setStatus("Add the STT and TTS model IDs to .env, then restart the server.");
      } else {
        connectionLabel.textContent = "Voice ready";
      }
    })
    .catch(() => {
      connectionLabel.textContent = "Offline";
    });
})();
