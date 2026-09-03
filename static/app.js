let currentJob = null;
let selectedFile = null;
let selectedFiles = [];
let selectedCodeFile = null;
let selectedScreenshots = [];

document.addEventListener("DOMContentLoaded", () => {
  loadConfig();
  loadHistory();
  setupDropzone();
  const dateInput = document.getElementById("dateInput");
  if (dateInput) {
    const today = new Date().toISOString().split("T")[0];
    dateInput.value = today;
  }
});

// Load Config from server
async function loadConfig() {
  try {
    const res = await fetch("/api/config");
    const data = await res.json();
    
    const badge = document.getElementById("statusBadge");
    const statusText = document.getElementById("statusText");

    if (data.gemini_api_key) {
      badge.className = "status-badge";
      statusText.innerText = `Gemini API активен (${data.model_name || "flash"})`;
    } else {
      badge.className = "status-badge warning";
      statusText.innerText = "Демо-режим (ключ не задан)";
    }

    // Populate settings form
    if (data.gemini_api_key) {
      document.getElementById("cfgApiKey").placeholder = data.masked_api_key || "Ключ сохранен";
    }
    if (data.model_name) document.getElementById("cfgModel").value = data.model_name;
    if (data.student) {
      document.getElementById("cfgFio").value = data.student.student_name || "";
      document.getElementById("cfgGroup").value = data.student.group || "";
      document.getElementById("cfgTeacher").value = data.student.teacher_name || "";
      document.getElementById("cfgInst").value = data.student.institution || "";
      document.getElementById("cfgSpec").value = data.student.specialty || "";
    }
  } catch (err) {
    console.error("Config load error:", err);
  }
}

// History loader
async function loadHistory() {
  try {
    const res = await fetch("/api/history");
    const list = await res.json();
    const container = document.getElementById("historyList");
    if (!list || list.length === 0) {
      container.innerHTML = '<span style="color: var(--text-muted); font-size: 13px;">История пуста</span>';
      return;
    }
    container.innerHTML = list.map(item => `
      <a href="${item.docx_url}" class="pill" style="text-decoration: none; padding: 6px 12px; display: inline-flex; align-items: center; gap: 6px;" download>
        📄 ${item.docx_filename}
      </a>
    `).join("");
  } catch (e) {
    console.error("History load error:", e);
  }
}

// Drag and drop setup
function setupDropzone() {
  const dropzone = document.getElementById("dropzone");
  const sDropzone = document.getElementById("screenshotDropzone");

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  [dropzone, sDropzone].forEach(zone => {
    if (!zone) return;
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(ev => {
      zone.addEventListener(ev, preventDefaults, false);
    });
    ['dragenter', 'dragover'].forEach(ev => {
      zone.addEventListener(ev, () => zone.classList.add("dragover"), false);
    });
    ['dragleave', 'drop'].forEach(ev => {
      zone.addEventListener(ev, () => zone.classList.remove("dragover"), false);
    });
  });

  if (dropzone) {
    dropzone.addEventListener("drop", e => {
      const dt = e.dataTransfer;
      if (dt.files.length > 0) addReferenceFiles(Array.from(dt.files));
    });
  }

  if (sDropzone) {
    sDropzone.addEventListener("drop", e => {
      const dt = e.dataTransfer;
      if (dt.files.length > 0) addScreenshots(Array.from(dt.files));
    });
  }
}

function handleCodeFileSelect(event) {
  if (event.target.files.length > 0) {
    const file = event.target.files[0];
    selectedCodeFile = file;
    const indicator = document.getElementById("codeFileSelected");
    const sizeKb = (file.size / 1024).toFixed(1);
    indicator.innerText = "✓ Выбран файл с кодом: " + file.name + " (" + sizeKb + " КБ)";
    indicator.style.display = "block";
    
    const reader = new FileReader();
    reader.onload = (e) => {
      document.getElementById("customCode").value = e.target.result;
    };
    reader.readAsText(file);
  }
}

function handleScreenshotsSelect(event) {
  const files = Array.from(event.target.files);
  addScreenshots(files);
}

function addScreenshots(files) {
  files.forEach(f => {
    if (f.type.startsWith("image/") || f.name.match(/\.(png|jpe?g|webp|bmp)$/i)) {
      selectedScreenshots.push(f);
    }
  });
  renderScreenshotPreviews();
}

function removeScreenshot(index, e) {
  if (e) e.stopPropagation();
  selectedScreenshots.splice(index, 1);
  renderScreenshotPreviews();
}

function renderScreenshotPreviews() {
  const container = document.getElementById("screenshotPreviews");
  const text = document.getElementById("screenshotDropzoneText");
  if (!container) return;
  container.innerHTML = "";

  if (selectedScreenshots.length === 0) {
    text.style.display = "block";
    return;
  }

  text.style.display = "none";
  selectedScreenshots.forEach((file, i) => {
    const chip = document.createElement("div");
    chip.className = "pill";
    chip.style.display = "inline-flex";
    chip.style.alignItems = "center";
    chip.style.gap = "6px";
    chip.style.fontSize = "12px";
    chip.style.padding = "4px 8px";
    chip.style.background = "rgba(59, 130, 246, 0.2)";
    chip.style.border = "1px solid rgba(59, 130, 246, 0.4)";
    chip.innerHTML = "🖼️ " + file.name.substring(0, 16) + "... <span onclick=\"removeScreenshot(" + i + ", event)\" style=\"cursor: pointer; font-weight: bold; color: #f87171; margin-left: 4px;\">&times;</span>";
    container.appendChild(chip);
  });
}

function handleFilesSelect(event) {
  const files = Array.from(event.target.files);
  addReferenceFiles(files);
}

function handleFileSelect(event) {
  handleFilesSelect(event);
}

function addReferenceFiles(files) {
  files.forEach(f => {
    if (!selectedFiles.some(existing => existing.name === f.name && existing.size === f.size)) {
      selectedFiles.push(f);
    }
  });
  renderFilesSelectedList();
}

function removeReferenceFile(index, e) {
  if (e) e.stopPropagation();
  selectedFiles.splice(index, 1);
  renderFilesSelectedList();
}

function renderFilesSelectedList() {
  const container = document.getElementById("filesSelectedList");
  const text = document.getElementById("dropzoneText");
  if (!container) return;
  container.innerHTML = "";

  if (selectedFiles.length === 0) {
    text.style.display = "block";
    return;
  }

  text.style.display = "none";
  selectedFiles.forEach((file, i) => {
    const chip = document.createElement("div");
    chip.className = "pill";
    chip.style.display = "inline-flex";
    chip.style.alignItems = "center";
    chip.style.gap = "6px";
    chip.style.fontSize = "12px";
    chip.style.padding = "4px 8px";
    chip.style.background = "rgba(14, 165, 233, 0.2)";
    chip.style.border = "1px solid rgba(14, 165, 233, 0.4)";

    let icon = "📄";
    const nameLow = file.name.toLowerCase();
    if (nameLow.endsWith(".pdf")) icon = "📕";
    else if (nameLow.endsWith(".docx") || nameLow.endsWith(".doc")) icon = "📝";
    else if (nameLow.match(/\.(png|jpe?g|webp|bmp)$/)) icon = "🖼️";

    const sizeKb = (file.size / 1024).toFixed(1);
    chip.innerHTML = icon + " " + file.name.substring(0, 20) + " (" + sizeKb + " КБ) <span onclick=\"removeReferenceFile(" + i + ", event)\" style=\"cursor: pointer; font-weight: bold; color: #f87171; margin-left: 4px;\">&times;</span>";
    container.appendChild(chip);
  });
}

function setSubject(name) {
  document.getElementById("subjectInput").value = name;
}

// Generate Lab Form Submit
async function generateLab(e) {
  e.preventDefault();

  const submitBtn = document.getElementById("submitBtn");
  const progressBox = document.getElementById("progressBox");
  const logList = document.getElementById("logList");
  const placeholder = document.getElementById("resultPlaceholder");
  const content = document.getElementById("resultContent");

  submitBtn.disabled = true;
  submitBtn.innerText = "⏳ Выполняется генерация...";
  progressBox.style.display = "block";
  logList.innerHTML = "";

  function addLog(text) {
    const li = document.createElement("li");
    li.innerText = text;
    logList.appendChild(li);
  }

  addLog("1. Анализ входного задания и методички...");

  const formData = new FormData();
  formData.append("subject", document.getElementById("subjectInput").value);
  formData.append("variant", document.getElementById("variantInput").value);
  const fnInput = document.getElementById("filenameInput");
  if (fnInput && fnInput.value.trim()) {
    formData.append("custom_filename", fnInput.value.trim());
  }
  formData.append("date_str", document.getElementById("dateInput").value);
  formData.append("include_theory", document.getElementById("theoryCheckbox").checked);
  formData.append("task_text", document.getElementById("taskText").value);
  const instrInput = document.getElementById("instructionsInput");
  const noCodeCb = document.getElementById("noCodeCheckbox");
  let customInstr = instrInput && instrInput.value.trim() ? instrInput.value.trim() : "";
  if (noCodeCb && noCodeCb.checked) {
    customInstr = "ЭТО РАБОТА ПО ДИЗАЙНУ / МОДЕЛИРОВАНИЮ БЕЗ КОДА. Код в отчете строго НЕ нужен (поле 'code' должно быть пустым '')! Сфокусируйся на проектных решениях, макетах экранов, сетке, типографике, палитре и компонентах! " + customInstr;
  }
  if (customInstr) {
    formData.append("custom_instructions", customInstr);
  }
  formData.append("with_title_page", document.getElementById("titlePageCheckbox").checked);

  if (selectedFile) {
    formData.append("file", selectedFile);
  }
  selectedFiles.forEach(f => {
    formData.append("files", f);
  });

  const customCodeVal = document.getElementById("customCode").value;
  if (customCodeVal && customCodeVal.trim()) {
    formData.append("custom_code", customCodeVal.trim());
  }
  if (selectedCodeFile) {
    formData.append("code_file", selectedCodeFile);
  }
  selectedScreenshots.forEach(shot => {
    formData.append("screenshots", shot);
  });

  addLog("2. Отправка запроса к Gemini API (анализ, синтез кода и ГОСТ-структуры)...");

  try {
    const res = await fetch("/api/generate", {
      method: "POST",
      body: formData
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Ошибка сервера при генерации");
    }

    const data = await res.json();
    currentJob = data;

    logList.innerHTML = "";
    if (data.steps && data.steps.length > 0) {
      data.steps.forEach(s => addLog(s));
    } else {
      addLog("✓ Готово! Лабораторная работа успешно сформирована.");
    }

    // Update Result View
    placeholder.style.display = "none";
    content.style.display = "block";

    // Download button
    const dlBtn = document.getElementById("downloadBtn");
    dlBtn.href = data.docx_url;
    dlBtn.innerText = `📥 Скачать ${data.docx_filename}`;

    // Screenshot tab
    document.getElementById("previewImage").src = data.screenshot_url;
    const figTitle = data.solution.figures && data.solution.figures[0] ? data.solution.figures[0].title : "Результат выполнения программы в консоли";
    document.getElementById("previewCaption").innerText = `Рисунок 1 – ${figTitle}`;

    // Code tab
    document.getElementById("previewCode").innerText = data.solution.code || "";

    // Report tab
    document.getElementById("repTopic").innerText = data.solution.topic || "";
    document.getElementById("repGoal").innerText = data.solution.goal || "";
    document.getElementById("repEquip").innerText = data.solution.equipment || "";
    document.getElementById("repConclusion").innerText = data.solution.conclusion || "";

    // Questions
    const qContainer = document.getElementById("repQuestions");
    if (data.solution.questions_answers && data.solution.questions_answers.length > 0) {
      qContainer.innerHTML = data.solution.questions_answers.map((qa, i) => `
        <div style="margin-bottom: 8px;">
          <strong style="color: var(--text);">${i + 1}. ${qa.question}</strong><br>
          <span>${qa.answer}</span>
        </div>
      `).join("");
    } else {
      qContainer.innerHTML = "<em>Контрольные вопросы не указаны в методичке</em>";
    }

    loadHistory();

  } catch (err) {
    addLog("❌ Ошибка: " + err.message);
    alert("Ошибка генерации: " + err.message);
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerText = "🚀 Сгенерировать работу по ГОСТу";
  }
}

// Tab switcher
function switchTab(tabId) {
  document.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("active"));
  document.querySelectorAll(".tab-panel").forEach(panel => panel.classList.remove("active"));
  
  event.target.classList.add("active");
  document.getElementById(tabId).classList.add("active");
}

function copyCode() {
  const code = document.getElementById("previewCode").innerText;
  navigator.clipboard.writeText(code).then(() => {
    alert("Код скопирован в буфер обмена!");
  });
}

// Settings Modal
function openSettings() {
  document.getElementById("settingsModal").style.display = "flex";
}

function closeSettings() {
  document.getElementById("settingsModal").style.display = "none";
}

async function saveSettings(e) {
  e.preventDefault();
  const apiKey = document.getElementById("cfgApiKey").value;
  const modelName = document.getElementById("cfgModel").value;
  const fio = document.getElementById("cfgFio").value;
  const group = document.getElementById("cfgGroup").value;
  const teacher = document.getElementById("cfgTeacher").value;
  const inst = document.getElementById("cfgInst").value;
  const spec = document.getElementById("cfgSpec").value;

  const payload = {
    model_name: modelName,
    student_name: fio,
    group: group,
    teacher_name: teacher,
    institution: inst,
    specialty: spec
  };

  if (apiKey.trim()) {
    payload.gemini_api_key = apiKey.trim();
  }

  try {
    const res = await fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("Ошибка сохранения");
    closeSettings();
    loadConfig();
    alert("Настройки успешно сохранены!");
  } catch (err) {
    alert("Не удалось сохранить настройки: " + err.message);
  }
}
