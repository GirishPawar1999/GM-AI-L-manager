/* -----------------------------
   Data & Initial setup
   ----------------------------- */
let emails = window.emailsData || []; // Emails from server

// labels: user-created labels (shown above default labels)
let labels = []; // each label: { name, color }

// app state
let state = {
    view: 'inbox',
    page: 1,
    pageSize: 5,
    search: '',
    selectedEmailId: null,
    sidebarCollapsed: false,
    latestNewEmailId: null
};

/* -----------------------------
   DOM helpers & Utilities
   ----------------------------- */

function $(id) { return document.getElementById(id); }

// Utility to check if body is HTML
function isHTML(str) {
    const htmlRegex = /<\/?[a-z][\s\S]*>/i;
    return htmlRegex.test(str);
}

// Utility to strip HTML tags
function stripHTML(html) {
    const tmp = document.createElement('DIV');
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText || '';
}

function formatPreview(email) {
    // Always restrict to 100 chars
    let preview = email.preview || email.snippet || '';
    if (preview.length > 100) {
        preview = preview.substring(0, 100) + '...';
    }
    return preview;
}

/* Basic heuristic sentiment: counts positive vs negative words */
const POS_WORDS = ['good', 'great', 'thanks', 'thank', 'congrat', 'congratulations', 'appreciate', 'awesome', 'love', 'happy', 'well done', 'success', 'pleased', 'best'];
const NEG_WORDS = ['not', 'unfortunately', 'sorry', 'problem', 'issue', 'delay', 'fail', 'unable', 'cancel', 'angry', 'hate', 'bad', 'concern'];

function detectTone(text) {
    if (!text) return 'Neutral';
    const t = text.toLowerCase();
    let pos = 0, neg = 0;
    POS_WORDS.forEach(w => { if (t.includes(w)) pos++; });
    NEG_WORDS.forEach(w => { if (t.includes(w)) neg++; });
    if (pos > neg + 0) return 'Positive';
    if (neg > pos + 0) return 'Negative';
    return 'Neutral';
}

function summarizeText(text, maxChars = 140) {
    if (!text) return '';
    if (text.length <= maxChars) return text;
    return text.slice(0, maxChars).trim() + '…';
}

/* -----------------------------
   Rendering: emails, labels, counts
   ----------------------------- */

function getFilteredEmails() {
    const q = state.search.trim().toLowerCase();
    let list = [...emails];

    // view filters
    if (state.view === 'starred') {
        list = list.filter(e => e.starred);
    } else if (state.view === 'promotions') {
        list = list.filter(e => e.labels && e.labels.includes('promotions'));
    } else if (state.view === 'social') {
        list = list.filter(e => e.labels && e.labels.includes('social'));
    } else if (state.view === 'updates') {
        list = list.filter(e => e.labels && e.labels.includes('updates'));
    } else if (state.view === 'drafts') {
        list = list.filter(e => e.labels && e.labels.includes('draft'));
    } else if (state.view === 'trash') {
        list = list.filter(e => e.labels && e.labels.includes('trash'));
    }

    // search
    if (q) {
        list = list.filter(e => (e.sender + ' ' + e.subject + ' ' + (e.preview || '') + ' ' + (e.body || '')).toLowerCase().includes(q));
    }

    return list;
}

function renderEmails() {
    const listEl = $('email-list');
    const all = getFilteredEmails();
    const total = all.length;
    const pageSize = state.pageSize;
    const pageCount = Math.max(1, Math.ceil(total / pageSize));
    if (state.page > pageCount) state.page = pageCount;
    const start = (state.page - 1) * pageSize;
    const pageItems = all.slice(start, start + pageSize);

    // update counts
    $('inbox-count').textContent = emails.filter(e => e.unread).length;
    $('promotions-count').textContent = emails.filter(e => e.labels && e.labels.includes('promotions')).length;
    $('social-count').textContent = emails.filter(e => e.labels && e.labels.includes('social')).length;
    $('updates-count').textContent = emails.filter(e => e.labels && e.labels.includes('updates')).length;
    $('draft-count').textContent = emails.filter(e => e.labels && e.labels.includes('draft')).length;

    listEl.innerHTML = pageItems.map(email => {
        const preview = formatPreview(email);
        const newBadge = email.new_email ? '<span style="background:#34a853;color:white;padding:2px 6px;border-radius:4px;font-size:10px;margin-left:8px;font-weight:600;">NEW</span>' : '';
        
        return `
            <div class="email-item ${email.unread ? 'unread' : ''}" data-id="${email.id}">
                <div class="email-left">
                    <input type="checkbox" class="checkbox" data-id="${email.id}" onclick="event.stopPropagation()" />
                    <span class="star ${email.starred ? 'active' : ''}" data-id="${email.id}" onclick="toggleStarEvent(event, '${email.id}')">★</span>
                    <span class="email-sender">${escapeHtml(email.sender)}${newBadge}</span>
                </div>
                <div class="email-content">
                    <span class="email-subject">${escapeHtml(email.subject)}</span>
                    <span class="email-preview"> - ${escapeHtml(preview)}</span>
                    ${renderEmailLabelsInline(email)}
                </div>
                <div class="email-time">${email.time}</div>
            </div>
        `;
    }).join('');

    // attach click events
    Array.from(document.querySelectorAll('.email-item')).forEach(el => {
        el.addEventListener('click', () => openEmail(el.dataset.id));
    });

    renderPagination(total, pageCount);
}

function renderEmailLabelsInline(email) {
    if (!email.labels || email.labels.length === 0) return '';
    const pills = email.labels.slice(0, 2).map(l => {
        const color = (labels.find(x => x.name === l) || { color: null }).color;
        const style = color ? `style="background:${color};color:#fff;padding:2px 8px;border-radius:999px;font-size:11px;margin-left:6px;"` : `style="background:#f1f3f4;color:#5f6368;padding:2px 8px;border-radius:999px;font-size:11px;margin-left:6px;"`;
        return `<span ${style}>${escapeHtml(l)}</span>`;
    });
    return `<div style="margin-top:6px;">${pills.join('')}</div>`;
}

function renderLabels() {
    const list = $('labels-list');
    list.innerHTML = labels.map((label, idx) => `
        <div class="nav-item" data-custom-label="${label.name}">
            <span class="icon" style="width:18px;"><span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:${label.color};"></span></span>
            <span>${escapeHtml(label.name)}</span>
            <span class="count" style="margin-left:auto;">${emails.filter(e => e.labels && e.labels.includes(label.name)).length}</span>
        </div>
    `).join('');

    Array.from(document.querySelectorAll('[data-custom-label]')).forEach(el => {
        el.addEventListener('click', () => {
            state.view = el.dataset.customLabel;
            state.page = 1;
            setActiveNavForView(el.dataset.customLabel);
            renderEmails();
        });
    });
}

function renderManageLabels() {
    const manage = $('manage-labels-list');
    manage.innerHTML = labels.map((label, index) => `
        <div style="display:flex;align-items:center;justify-content:space-between;padding:8px;border:1px solid #dadce0;margin-bottom:8px;border-radius:6px;">
            <div style="display:flex;gap:8px;align-items:center;">
                <div style="width:14px;height:14px;border-radius:50%;background:${label.color};"></div>
                <div style="font-weight:600;">${escapeHtml(label.name)}</div>
            </div>
            <div>
                <button class="btn btn-secondary" onclick="deleteLabel(${index})">Delete</button>
            </div>
        </div>
    `).join('');
}

function renderPagination(total, pageCount) {
    const p = $('pagination');
    if (pageCount <= 1) { p.innerHTML = ''; return; }
    let html = '';
    for (let i = 1; i <= pageCount; i++) {
        html += `<button class="page-btn ${i === state.page ? 'active' : ''}" data-page="${i}">${i}</button>`;
    }
    p.innerHTML = html;
    Array.from(p.querySelectorAll('.page-btn')).forEach(btn => {
        btn.addEventListener('click', () => {
            state.page = Number(btn.dataset.page);
            renderEmails();
        });
    });
}

/* -----------------------------
   Email open / reply / compose
   ----------------------------- */

function openEmail(id) {
    const email = emails.find(e => e.id === id);
    if (!email) return;
    state.selectedEmailId = id;
    
    // mark read and clear new_email flag
    email.unread = false;
    email.new_email = false;
    renderEmails();

    // populate detail panel
    $('detailSender').textContent = email.sender;
    $('detailSubject').textContent = email.subject;
    $('detailTime').textContent = email.time;
    
    // Display body: if not HTML, show full text in pre-wrap
    const bodyContent = email.body || email.snippet || '';
    if (isHTML(bodyContent)) {
        // If HTML, render as-is in iframe or sanitized div
        $('detailBody').innerHTML = `<div class="email-canvas">${bodyContent}</div>`;
    } else {
        // If plain text, show full text with pre-wrap
        $('detailBody').innerHTML = `<div class="plain-body">${escapeHtml(bodyContent)}</div>`;
    }

    // AI Summary section
    if (email.aiSummary) {
        const summaryHTML = `
            <div style="background:#e8f5e9;border-left:4px solid #34a853;padding:12px;margin-bottom:16px;border-radius:8px;">
                <div style="font-weight:600;color:#1e8e3e;margin-bottom:6px;">🤖 AI Summary</div>
                <div style="font-size:14px;color:#202124;line-height:1.6;">${escapeHtml(email.aiSummary.summary)}</div>
                <div style="margin-top:8px;font-size:12px;color:#5f6368;">
                    <span style="font-weight:600;">Tone:</span> 
                    <span class="tone ${email.aiSummary.tone.toLowerCase()}">${email.aiSummary.tone}</span>
                    <span style="margin-left:12px;font-weight:600;">Confidence:</span> ${Math.round(email.aiSummary.confidence * 100)}%
                </div>
            </div>
        `;
        $('detailBody').innerHTML = summaryHTML + $('detailBody').innerHTML;
    }

    // replies
    renderRepliesForEmail(email);

    $('replyText').value = '';
    $('replyTone').textContent = '';

    const panel = $('detailPanel');
    panel.classList.remove('detail-hidden');
    panel.scrollTop = 0;
}

function closeDetail() {
    state.selectedEmailId = null;
    $('detailPanel').classList.add('detail-hidden');
}

function renderRepliesForEmail(email) {
    const el = $('detailReplies');
    if (!email.replies) email.replies = [];
    el.innerHTML = email.replies.map(r => `
        <div class="reply">
            <div class="reply-meta">${escapeHtml(r.from)} • ${escapeHtml(r.time)} • Tone: ${escapeHtml(r.tone)}</div>
            <div>${escapeHtml(r.text)}</div>
        </div>
    `).join('');
}

function sendReply() {
    const text = $('replyText').value.trim();
    if (!text) { alert('Reply cannot be empty'); return; }
    const email = emails.find(e => e.id === state.selectedEmailId);
    if (!email) { alert('No email selected'); return; }
    const tone = detectTone(text);
    const replyObj = { from: 'You', time: new Date().toLocaleString(), text, tone };
    email.replies = email.replies || [];
    email.replies.push(replyObj);
    renderRepliesForEmail(email);
    $('replyText').value = '';
    $('replyTone').textContent = tone;
}

function insertReplyTemplate(template) {
    const area = $('replyText');
    area.value = (area.value ? area.value + '\n\n' : '') + template;
}

/* Compose drawer open/close and actions */
function openCompose() {
    $('composeDrawer').classList.add('open');
    $('composeDrawer').setAttribute('aria-hidden', 'false');
    updateComposeTone();
}
function closeCompose() {
    $('composeDrawer').classList.remove('open');
    $('composeDrawer').setAttribute('aria-hidden', 'true');
}

function saveDraft() {
    const to = $('composeTo').value.trim();
    const subj = $('composeSubject').value.trim();
    const body = $('composeBody').value.trim();
    const id = 'draft_' + Date.now();
    emails.unshift({ id, sender: to || 'Draft', subject: subj || '(no subject)', preview: body.slice(0, 100), time: 'Draft', unread: false, starred: false, labels: ['draft'], body, snippet: body.slice(0, 100), replies: [], new_email: false });
    closeCompose();
    renderEmails();
    alert('Saved to Drafts');
}

function sendCompose() {
    const to = $('composeTo').value.trim();
    const subj = $('composeSubject').value.trim();
    const body = $('composeBody').value.trim();
    if (!to && !subj && !body) { alert('Cannot send empty email'); return; }

    const id = 'sent_' + Date.now();
    const newEmail = { id, sender: to || 'Me', subject: subj || '(no subject)', preview: body.slice(0, 100), time: 'Now', unread: false, starred: false, labels: ['sent'], body, snippet: body.slice(0, 100), replies: [], new_email: false };
    emails.unshift(newEmail);

    const incomingId = 'inbox_' + (Date.now() + 1);
    const incoming = { id: incomingId, sender: to || 'no-reply@example.com', subject: 'Re: ' + (subj || '(no subject)'), preview: summarizeText(body, 100), time: 'Now', unread: true, starred: false, labels: [], body, snippet: body.slice(0, 100), replies: [], new_email: true };
    emails.unshift(incoming);
    state.latestNewEmailId = incomingId;

    closeCompose();
    renderEmails();
    showNewMailPopup(incoming);
    resetComposeFields();
}

function resetComposeFields() {
    $('composeTo').value = '';
    $('composeSubject').value = '';
    $('composeBody').value = '';
    updateComposeTone();
}

function updateComposeTone() {
    const text = ($('composeSubject').value || '') + ' ' + ($('composeBody').value || '');
    const tone = detectTone(text);
    $('composeToneLabel').textContent = tone;
    $('composeTonePill').textContent = tone;
    if (tone === 'Positive') $('composeTonePill').style.background = '#dff6e3';
    else if (tone === 'Negative') $('composeTonePill').style.background = '#ffe5e5';
    else $('composeTonePill').style.background = '#f1f3f4';
}

function showNewMailPopup(email) {
    if (!email) return;
    $('newMailSummary').textContent = summarizeText(email.preview || email.body || email.subject, 200);
    $('newMailTone').textContent = detectTone((email.preview || email.body || email.subject));
    $('newMailPopup').classList.add('show');
}
function dismissNewMailPopup() {
    $('newMailPopup').classList.remove('show');
}
function openLatestNewEmail() {
    if (state.latestNewEmailId) openEmail(state.latestNewEmailId);
    dismissNewMailPopup();
}

function toggleSidebar() {
    const bar = $('sidebar');
    bar.classList.toggle('collapsed');
    state.sidebarCollapsed = bar.classList.contains('collapsed');
}

function openCreateLabelModal() {
    $('createLabelModal').classList.add('show');
}
function closeCreateLabelModal() {
    $('createLabelModal').classList.remove('show');
    $('labelName').value = '';
}
function createLabel() {
    const name = $('labelName').value.trim();
    const color = $('labelColor').value;
    if (!name) { alert('Please enter a label name'); return; }
    if (labels.some(l => l.name.toLowerCase() === name.toLowerCase())) { alert('Label already exists'); return; }
    labels.unshift({ name, color });
    renderLabels();
    closeCreateLabelModal();
}
function openManageLabelsModal() {
    renderManageLabels();
    $('manageLabelsModal').classList.add('show');
}
function closeManageLabelsModal() {
    $('manageLabelsModal').classList.remove('show');
}
function deleteLabel(index) {
    const lb = labels[index];
    if (!confirm(`Delete label "${lb.name}"? This will remove the label from any emails.`)) return;
    labels.splice(index, 1);
    emails.forEach(e => { if (e.labels) e.labels = e.labels.filter(x => x !== lb.name); });
    renderLabels(); renderManageLabels(); renderEmails();
}

function toggleStarEvent(ev, id) {
    ev.stopPropagation();
    const e = emails.find(x => x.id === id);
    if (e) { e.starred = !e.starred; renderEmails(); }
}

function simulateNewEmail() {
    const id = 'sim_' + Date.now();
    const sample = {
        id,
        sender: 'noreply+update@example.com',
        subject: 'Important update to your account',
        preview: 'We updated our terms – please review the changes to stay compliant.',
        time: new Date().toLocaleString(),
        unread: true,
        starred: false,
        labels: ['updates'],
        body: 'We have updated the terms of service. Please review the changes at your convenience.',
        snippet: 'We updated our terms – please review the changes to stay compliant.',
        replies: [],
        new_email: true,
        aiSummary: {
            summary: 'Important account update regarding terms of service changes.',
            tone: 'Neutral',
            confidence: 0.85
        }
    };
    emails.unshift(sample);
    state.latestNewEmailId = id;
    renderEmails();
    showNewMailPopup(sample);
}

function setActiveNavForView(view) {
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const found = Array.from(document.querySelectorAll('.nav-item')).find(n => {
        return n.dataset.view === view || n.dataset.label === view || n.dataset.customLabel === view;
    });
    if (found) found.classList.add('active');

    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    const tabEl = Array.from(document.querySelectorAll('.tab')).find(t => t.dataset.tab === view || (view === 'inbox' && t.dataset.tab === 'primary'));
    if (tabEl) tabEl.classList.add('active');
}

function changeView(view) {
    state.view = view;
    state.page = 1;
    setActiveNavForView(view);
    renderEmails();
}

function applySearch() {
    const q = $('searchInput').value || '';
    state.search = q;
    state.page = 1;
    renderEmails();
}

function escapeHtml(unsafe) {
    if (unsafe === undefined || unsafe === null) return '';
    return unsafe.toString().replace(/[&<"'>]/g, function (m) {
        return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' })[m];
    });
}

/* page init & event wiring */
(function init() {
    renderLabels();
    renderEmails();

    $('menuToggle').addEventListener('click', toggleSidebar);
    $('composeOpenBtn').addEventListener('click', openCompose);
    $('composeCloseBtn').addEventListener('click', closeCompose);
    $('sendComposeBtn').addEventListener('click', sendCompose);
    $('saveDraftBtn').addEventListener('click', saveDraft);
    $('attachBtn').addEventListener('click', () => alert('Attach not implemented in demo'));
    $('addLabelBtn').addEventListener('click', openCreateLabelModal);
    $('simulateNewMailBtn').addEventListener('click', simulateNewEmail);

    $('searchInput').addEventListener('input', function () { state.search = this.value; state.page = 1; renderEmails(); });

    ['composeSubject', 'composeBody'].forEach(id => {
        $(id).addEventListener('input', updateComposeTone);
    });

    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tb = tab.dataset.tab;
            changeView(tb === 'primary' ? 'inbox' : tb);
        });
    });

    document.querySelectorAll('.modal').forEach(m => m.addEventListener('click', (ev) => {
        if (ev.target === m) m.classList.remove('show');
    }));

    document.addEventListener('keydown', (ev) => {
        if (ev.key === 'c' && !ev.metaKey && !ev.ctrlKey) { openCompose(); }
    });

    document.addEventListener('keydown', (ev) => {
        if (ev.key === 'Escape') { closeCompose(); closeDetail(); dismissNewMailPopup(); }
    });

    // Auto-refresh emails every 60 seconds
    setInterval(() => {
        console.log('🔄 Refreshing emails...');
        window.location.reload();
    }, 60000);
})();

function openManageLabelsModal() {
    renderManageLabels();
    $('manageLabelsModal').classList.add('show');
}

function openAISettings() { $('aiSettingsModal').classList.add('show'); }
function closeAISettings() { $('aiSettingsModal').classList.remove('show'); }

function toggleProfileMenu() {
    alert('Profile menu would open here!\n\nGirish Pawar\ngirish.pawar@gmail.com');
}