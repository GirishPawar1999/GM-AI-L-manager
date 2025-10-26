const fs = require("fs");
const path = require("path");
const express = require("express");
const readline = require("readline");
const { google } = require("googleapis");
const { spawn } = require("child_process");

const app = express();
const PORT = 3000;

app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));
app.use(express.static(path.join(__dirname, "views")));
app.use(express.json());

const SCOPES = [
  "https://www.googleapis.com/auth/gmail.readonly",
  "https://www.googleapis.com/auth/gmail.send",
  "https://www.googleapis.com/auth/gmail.compose"
];
const TOKEN_PATH = "token.json";
const DATABASE_PATH = "database.json";
const TEMPLATE_PATH = "template.json";
const AI_SETTINGS_PATH = "AI_settings.json";

/* ---------------------------------------------------------
   🟢 1. Ensure files exist on startup
--------------------------------------------------------- */
if (!fs.existsSync(TEMPLATE_PATH)) {
  const defaultTemplate = {
    rules: [
      { category: "Work", keywords: ["meeting", "project", "deadline", "report", "presentation"] },
      { category: "Bills", keywords: ["invoice", "payment", "bill", "due", "subscription"] },
      { category: "Shopping", keywords: ["order", "shipped", "delivery", "purchase", "cart"] }
    ]
  };
  fs.writeFileSync(TEMPLATE_PATH, JSON.stringify(defaultTemplate, null, 2));
  console.log("🆕 Created default template.json");
}

if (!fs.existsSync(AI_SETTINGS_PATH)) {
  const defaultSettings = {
    emailSummarization: true,
    aiAutoCategorization: true,
    smartReplyGeneration: true
  };
  fs.writeFileSync(AI_SETTINGS_PATH, JSON.stringify(defaultSettings, null, 2));
  console.log("🆕 Created default AI_settings.json");
}

/* ---------------------------------------------------------
   AI Settings Management
--------------------------------------------------------- */
function loadAISettings() {
  try {
    if (fs.existsSync(AI_SETTINGS_PATH)) {
      const data = fs.readFileSync(AI_SETTINGS_PATH, "utf8");
      return JSON.parse(data);
    }
  } catch (err) {
    console.error("Error loading AI settings:", err);
  }
  return {
    emailSummarization: true,
    aiAutoCategorization: true,
    smartReplyGeneration: true
  };
}

function saveAISettings(settings) {
  try {
    fs.writeFileSync(AI_SETTINGS_PATH, JSON.stringify(settings, null, 2));
    console.log("✅ AI Settings saved successfully");
    return true;
  } catch (err) {
    console.error("Error saving AI settings:", err);
    return false;
  }
}

/* ---------------------------------------------------------
   Template/Rules Management
--------------------------------------------------------- */
function loadTemplates() {
  try {
    if (fs.existsSync(TEMPLATE_PATH)) {
      const data = fs.readFileSync(TEMPLATE_PATH, "utf8");
      return JSON.parse(data);
    }
  } catch (err) {
    console.error("Error loading templates:", err);
  }
  return { rules: [] };
}

function saveTemplates(data) {
  try {
    fs.writeFileSync(TEMPLATE_PATH, JSON.stringify(data, null, 2));
    console.log("✅ Templates saved successfully");
  } catch (err) {
    console.error("Error saving templates:", err);
  }
}

function categorizeEmail(subject, body, snippet, templates) {
  const text = (subject + " " + body + " " + snippet).toLowerCase();
  const categories = [];

  templates.rules.forEach((rule) => {
    const matched = rule.keywords.some((kw) => text.includes(kw.toLowerCase()));
    if (matched) categories.push(rule.category.toLowerCase());
  });

  return categories;
}

/* ---------------------------------------------------------
   Database helpers
--------------------------------------------------------- */
function loadDatabase() {
  try {
    if (fs.existsSync(DATABASE_PATH)) {
      const data = fs.readFileSync(DATABASE_PATH, "utf8");
      return JSON.parse(data);
    }
  } catch (err) {
    console.error("Error loading database:", err);
  }
  return { emails: [], lastSync: null };
}

function saveDatabase(data) {
  try {
    fs.writeFileSync(DATABASE_PATH, JSON.stringify(data, null, 2));
    console.log("✅ Database saved successfully");
  } catch (err) {
    console.error("Error saving database:", err);
  }
}

/* ---------------------------------------------------------
   Gmail Auth helpers with error handling
--------------------------------------------------------- */
function authorize(credentials, callback) {
  const creds = credentials.installed || credentials.web;
  const { client_secret, client_id, redirect_uris } = creds;
  const oAuth2Client = new google.auth.OAuth2(
    client_id,
    client_secret,
    redirect_uris[0]
  );

  fs.readFile(TOKEN_PATH, (err, token) => {
    if (err) return getAccessToken(oAuth2Client, callback);
    oAuth2Client.setCredentials(JSON.parse(token));
    callback(oAuth2Client);
  });
}

function getAccessToken(oAuth2Client, callback) {
  const authUrl = oAuth2Client.generateAuthUrl({
    access_type: "offline",
    scope: SCOPES,
  });
  console.log("Authorize this app by visiting this URL:", authUrl);

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });
  rl.question("Enter the code from that page here: ", (code) => {
    rl.close();
    oAuth2Client.getToken(code, (err, token) => {
      if (err) return console.error("Error retrieving access token", err);
      oAuth2Client.setCredentials(token);
      fs.writeFileSync(TOKEN_PATH, JSON.stringify(token));
      callback(oAuth2Client);
    });
  });
}

/* ---------------------------------------------------------
   Extract body from Gmail messages
--------------------------------------------------------- */
function extractBody(payload) {
  let result = "";
  if (payload.parts) {
    for (const part of payload.parts) result += extractBody(part);
  } else if (payload.mimeType === "text/plain" && payload.body?.data) {
    result += Buffer.from(payload.body.data, "base64").toString("utf8") + "\n";
  } else if (payload.mimeType === "text/html" && payload.body?.data) {
    let html = Buffer.from(payload.body.data, "base64").toString("utf8");
    html = html.replace(/<!--[\s\S]*?-->/g, "");
    html = html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, "");
    html = html.replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, "");
    result += html + "\n";
  }
  return result;
}

/* ---------------------------------------------------------
   Fetch emails with thread support
--------------------------------------------------------- */
async function listMessages(auth) {
  const gmail = google.gmail({ version: "v1", auth });
  const emails = [];
  const templates = loadTemplates();

  try {
    const res = await gmail.users.messages.list({ userId: "me", maxResults: 50 });
    const messages = res.data.messages || [];
    if (!messages.length) return emails;

    console.log(`📧 Fetching ${messages.length} emails...`);

    const emailPromises = messages.map(async (msg, i) => {
      try {
        const emailData = await gmail.users.messages.get({ userId: "me", id: msg.id, format: "full" });
        const headers = emailData.data.payload.headers;
        const from = headers.find(h => h.name === "From")?.value || "";
        const subject = headers.find(h => h.name === "Subject")?.value || "";
        const date = headers.find(h => h.name === "Date")?.value || "";
        const snippet = emailData.data.snippet || "";
        const body = extractBody(emailData.data.payload);
        const labels = emailData.data.labelIds || [];
        const isUnread = labels.includes("UNREAD");
        const threadId = emailData.data.threadId;

        const mappedLabels = [];
        labels.forEach(l => {
          if (l === "CATEGORY_PROMOTIONS") mappedLabels.push("promotions");
          else if (l === "CATEGORY_SOCIAL") mappedLabels.push("social");
          else if (l === "CATEGORY_UPDATES") mappedLabels.push("updates");
          else if (l === "DRAFT") mappedLabels.push("draft");
          else if (l === "SENT") mappedLabels.push("sent");
          else if (l === "TRASH") mappedLabels.push("trash");
          else if (l === "STARRED") mappedLabels.push("starred");
          else if (l === "INBOX") mappedLabels.push("inbox");
        });

        const customCategories = categorizeEmail(subject, body, snippet, templates);
        const allLabels = [...new Set([...mappedLabels, ...customCategories])];

        const time = new Date(date).toLocaleDateString("en-US", { month: "short", day: "numeric" });

        return {
          id: msg.id,
          threadId: threadId,
          sender: from,
          subject,
          preview: snippet.substring(0, 100) + (snippet.length > 100 ? "..." : ""),
          time,
          unread: isUnread,
          starred: labels.includes("STARRED"),
          labels: allLabels,
          body,
          snippet,
          replies: [],
          new_email: false,
        };
      } catch (err) {
        console.error("Error processing email:", err.message);
        return null;
      }
    });

    const results = await Promise.all(emailPromises);
    return results.filter(Boolean);
  } catch (err) {
    console.error("Error fetching emails:", err.message);
    if (err.code === 'ETIMEDOUT' || err.code === 'ENOTFOUND') {
      console.error("⚠️ Network error - please check your internet connection");
    }
    return emails;
  }
}

/* ---------------------------------------------------------
   Send Email via Gmail API
--------------------------------------------------------- */
async function sendEmail(auth, to, subject, body, threadId = null) {
  const gmail = google.gmail({ version: "v1", auth });
  
  try {
    const emailLines = [
      `To: ${to}`,
      `Subject: ${subject}`,
      "Content-Type: text/html; charset=utf-8",
      "",
      body
    ];
    
    const email = emailLines.join("\r\n");
    const encodedEmail = Buffer.from(email).toString("base64").replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    
    const params = {
      userId: "me",
      requestBody: {
        raw: encodedEmail
      }
    };
    
    if (threadId) {
      params.requestBody.threadId = threadId;
    }
    
    const result = await gmail.users.messages.send(params);
    console.log("✅ Email sent successfully:", result.data.id);
    return { success: true, messageId: result.data.id };
    
  } catch (err) {
    console.error("Error sending email:", err.message);
    return { success: false, error: err.message };
  }
}

/* ---------------------------------------------------------
   Run Python AI Processing (Non-blocking)
--------------------------------------------------------- */
function runPythonAIProcessing() {
  return new Promise((resolve, reject) => {
    console.log("🤖 Running Python AI processing in background...");
    
    const pythonProcess = spawn("python", ["Summary_and_tone.py"], {
      detached: true,
      stdio: 'ignore'
    });
    
    pythonProcess.unref();
    
    console.log("✅ Python AI processing started in background");
    resolve();
  });
}

/* ---------------------------------------------------------
   Sync & categorize emails
--------------------------------------------------------- */
async function syncEmails(auth) {
  try {
    const db = loadDatabase();
    const existingIds = new Set(db.emails.map(e => e.id));
    const fetchedEmails = await listMessages(auth);

    if (!fetchedEmails || fetchedEmails.length === 0) {
      console.log("⚠️ No emails fetched");
      return db.emails;
    }

    const newEmails = fetchedEmails.filter(e => !existingIds.has(e.id));
    
    newEmails.forEach(e => e.new_email = true);
    
    db.emails = [...newEmails, ...db.emails.filter(e => fetchedEmails.find(f => f.id === e.id))];
    db.lastSync = new Date().toISOString();

    saveDatabase(db);
    
    const aiSettings = loadAISettings();
    if (aiSettings.emailSummarization && newEmails.length > 0) {
      runPythonAIProcessing().catch(err => {
        console.error("AI processing failed:", err.message);
      });
    }
    
    return db.emails;
  } catch (err) {
    console.error("Error in syncEmails:", err.message);
    const db = loadDatabase();
    return db.emails;
  }
}

/* ---------------------------------------------------------
   Category Counts
--------------------------------------------------------- */
function getCategoryCounts(emails) {
  const counts = {};
  emails.forEach(e => e.labels?.forEach(l => counts[l] = (counts[l] || 0) + 1));
  return counts;
}

/* ---------------------------------------------------------
   Routes
--------------------------------------------------------- */
app.get("/", async (req, res) => {
  try {
    if (!fs.existsSync("credentials.json")) {
      return res.status(500).send("Missing credentials.json file");
    }

    const content = fs.readFileSync("credentials.json", "utf8");
    const credentials = JSON.parse(content);

    authorize(credentials, async (auth) => {
      try {
        const emails = await syncEmails(auth);
        const templates = loadTemplates();
        const categoryCounts = getCategoryCounts(emails);
        const aiSettings = loadAISettings();

        const listSummary = emails.slice(0, 5).map(e => ({
          sender: e.sender,
          time: e.time,
          tone: e.aiSummary?.tone || "Neutral",
          summary: e.aiSummary?.summary || e.snippet,
        }));
        
        const bulkSummary = listSummary.map(e => 
          `${e.sender} (${e.time}): ${e.summary}`
        ).join("\n\n");

        res.render("dashboard", {
          emails,
          summary: JSON.stringify({ list: listSummary, bulk: bulkSummary }),
          templates,
          categoryCounts,
          aiSettings,
        });
      } catch (err) {
        console.error("Error in route handler:", err);
        res.status(500).send("Error fetching emails: " + err.message);
      }
    });
  } catch (err) {
    console.error("Error reading credentials:", err);
    res.status(500).send("Error reading credentials: " + err.message);
  }
});

app.post("/api/add-template", (req, res) => {
  const { category, keywords } = req.body;
  if (!category || !Array.isArray(keywords)) return res.status(400).json({ error: "Invalid template data" });

  const templates = loadTemplates();
  const existing = templates.rules.find(r => r.category.toLowerCase() === category.toLowerCase());
  if (existing) existing.keywords = [...new Set([...existing.keywords, ...keywords])];
  else templates.rules.push({ category, keywords });

  saveTemplates(templates);
  
  const db = loadDatabase();
  db.emails.forEach(email => {
    const customCategories = categorizeEmail(email.subject, email.body, email.snippet, templates);
    const existingLabels = email.labels.filter(l => !templates.rules.some(r => r.category.toLowerCase() === l));
    email.labels = [...new Set([...existingLabels, ...customCategories])];
  });
  saveDatabase(db);
  
  res.json({ success: true, templates });
});

app.post("/api/delete-template", (req, res) => {
  const { category } = req.body;
  if (!category) return res.status(400).json({ error: "Category name required" });

  const templates = loadTemplates();
  templates.rules = templates.rules.filter(r => r.category.toLowerCase() !== category.toLowerCase());
  saveTemplates(templates);
  
  const db = loadDatabase();
  db.emails.forEach(email => {
    email.labels = email.labels.filter(l => l !== category.toLowerCase());
  });
  saveDatabase(db);
  
  res.json({ success: true });
});

app.post("/api/save-ai-settings", (req, res) => {
  const { emailSummarization, aiAutoCategorization, smartReplyGeneration } = req.body;
  
  const settings = {
    emailSummarization: emailSummarization !== undefined ? emailSummarization : true,
    aiAutoCategorization: aiAutoCategorization !== undefined ? aiAutoCategorization : true,
    smartReplyGeneration: smartReplyGeneration !== undefined ? smartReplyGeneration : true
  };

  const success = saveAISettings(settings);
  res.json({ success });
});

app.post("/api/send-email", async (req, res) => {
  const { to, subject, body, threadId } = req.body;
  
  if (!to || !subject || !body) {
    return res.status(400).json({ error: "Missing required fields" });
  }

  try {
    if (!fs.existsSync("credentials.json")) {
      return res.status(500).json({ error: "Missing credentials.json file" });
    }

    const content = fs.readFileSync("credentials.json", "utf8");
    const credentials = JSON.parse(content);

    authorize(credentials, async (auth) => {
      const result = await sendEmail(auth, to, subject, body, threadId);
      
      if (result.success) {
        const db = loadDatabase();
        const newEmail = {
          id: result.messageId,
          threadId: threadId || result.messageId,
          sender: "Me",
          subject,
          preview: body.substring(0, 100),
          time: new Date().toLocaleDateString("en-US", { month: "short", day: "numeric" }),
          unread: false,
          starred: false,
          labels: ["sent"],
          body,
          snippet: body.substring(0, 100),
          replies: [],
          new_email: false
        };
        
        db.emails.unshift(newEmail);
        saveDatabase(db);
        
        res.json({ success: true, messageId: result.messageId });
      } else {
        res.status(500).json({ success: false, error: result.error });
      }
    });
  } catch (err) {
    console.error("Error in send-email API:", err);
    res.status(500).json({ error: err.message });
  }
});

app.post("/api/save-reply", (req, res) => {
  const { emailId, replyText, tone } = req.body;
  
  if (!emailId || !replyText) {
    return res.status(400).json({ error: "Missing required fields" });
  }

  try {
    const db = loadDatabase();
    const email = db.emails.find(e => e.id === emailId);
    
    if (!email) {
      return res.status(404).json({ error: "Email not found" });
    }

    if (!email.replies) {
      email.replies = [];
    }

    const reply = {
      from: "You",
      time: new Date().toLocaleString(),
      text: replyText,
      tone: tone || "Neutral"
    };

    email.replies.push(reply);
    saveDatabase(db);

    res.json({ success: true, reply });
  } catch (err) {
    console.error("Error saving reply:", err);
    res.status(500).json({ error: err.message });
  }
});

/* ---------------------------------------------------------
   Run Python on startup (in background)
--------------------------------------------------------- */
async function runInitialAIProcessing() {
  const db = loadDatabase();
  const aiSettings = loadAISettings();
  
  if (db.emails.length > 0 && aiSettings.emailSummarization) {
    console.log("🚀 Running initial AI processing on startup...");
    try {
      await runPythonAIProcessing();
      console.log("✅ Initial AI processing started");
    } catch (err) {
      console.error("⚠️ Initial AI processing failed:", err.message);
    }
  }
}

/* ---------------------------------------------------------
   Background sync with error handling
--------------------------------------------------------- */
function startBackgroundSync() {
  if (!fs.existsSync("credentials.json")) {
    console.error("❌ Missing credentials.json - background sync disabled");
    return;
  }

  try {
    const content = fs.readFileSync("credentials.json", "utf8");
    const credentials = JSON.parse(content);
    
    authorize(credentials, (auth) => {
      console.log("🔄 Background sync started");
      setInterval(async () => {
        try {
          await syncEmails(auth);
        } catch (err) {
          console.error("Background sync error:", err.message);
        }
      }, 60000);
    });
  } catch (err) {
    console.error("Error starting background sync:", err.message);
  }
}

/* ---------------------------------------------------------
   Start server
--------------------------------------------------------- */
app.listen(PORT, async () => {
  console.log(`✅ Server running at http://localhost:${PORT}`);
  await runInitialAIProcessing();
  startBackgroundSync();
});