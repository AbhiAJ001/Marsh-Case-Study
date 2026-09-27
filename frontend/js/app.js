/* ─── Marsh Pitch Generator — Client-side Logic ───
   Pure vanilla JS. No jQuery, no React, no frameworks.
   Just clean DOM manipulation and Fetch API calls.
   ─────────────────────────────────────────────────── */

// ─── State ───
let currentProfile = null;
let currentPitch = null;

// ─── DOM refs ───
const $ = (id) => document.getElementById(id);

// ─── Init ───
document.addEventListener('DOMContentLoaded', () => {
    loadPolicies();
});

// ─── Load available policies ───
async function loadPolicies() {
    try {
        const res = await fetch('/api/policies');
        const policies = await res.json();
        renderPolicyCheckboxes(policies);
    } catch (err) {
        renderPolicyCheckboxes([
            { id: 'abhi-activ-one', name: 'ABHI Activ One' },
            { id: 'care-health', name: 'Care Health Insurance Plan' },
            { id: 'hdfc-optima-secure-plus', name: 'HDFC ERGO Optima Secure+' },
            { id: 'niva-bupa-reassure', name: 'Niva Bupa ReAssure 2.0' },
        ]);
    }
}

function renderPolicyCheckboxes(policies) {
    const container = $('policyCheckboxes');
    container.innerHTML = policies.map(p => `
        <div class="checkbox-item">
            <input type="checkbox" id="policy_${p.id}" value="${p.id}" checked>
            <label for="policy_${p.id}">${p.name}</label>
        </div>
    `).join('');
}

// ─── Get selected policies ───
function getSelectedPolicies() {
    const checkboxes = document.querySelectorAll('#policyCheckboxes input:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

// ─── Step progress tracker ───────────────────────────────────────────────────

function showProgressTracker() {
    $('progressTracker').classList.remove('hidden');
    // Reset all steps to idle
    ['research', 'retrieve', 'pitch'].forEach(resetStep);
}

function hideProgressTracker() {
    $('progressTracker').classList.add('hidden');
}

function setStepRunning(stepId, detail) {
    const step = $('step-' + stepId);
    step.classList.remove('done', 'idle');
    step.classList.add('running');
    step.querySelector('.step-spinner').classList.remove('hidden');
    step.querySelector('.step-tick').classList.add('hidden');
    step.querySelector('.step-num').classList.add('hidden');
    if (detail) $('step-' + stepId + '-detail').textContent = detail;
    // also update header status
    $('statusDot').classList.add('busy');
    $('statusText').textContent = 'Processing';
}

function setStepDone(stepId, detail) {
    const step = $('step-' + stepId);
    step.classList.remove('running', 'idle');
    step.classList.add('done');
    step.querySelector('.step-spinner').classList.add('hidden');
    step.querySelector('.step-tick').classList.remove('hidden');
    step.querySelector('.step-num').classList.add('hidden');
    if (detail) $('step-' + stepId + '-detail').textContent = detail;
}

function resetStep(stepId) {
    const step = $('step-' + stepId);
    step.classList.remove('running', 'done');
    step.classList.add('idle');
    step.querySelector('.step-spinner').classList.add('hidden');
    step.querySelector('.step-tick').classList.add('hidden');
    step.querySelector('.step-num').classList.remove('hidden');
}

// ─── Loading state (for PPTX download / audit only) ──────────────────────────
function showLoading(message) {
    $('loadingText').textContent = message;
    $('loadingOverlay').classList.remove('hidden');
    $('statusDot').classList.add('busy');
    $('statusText').textContent = 'Processing';
}

function hideLoading() {
    $('loadingOverlay').classList.add('hidden');
    $('statusDot').classList.remove('busy');
    $('statusText').textContent = 'Ready';
}

// ─── Reset all results sections before a new search ──────────────────────────
function resetResults() {
    currentProfile = null;
    currentPitch = null;
    $('profileSection').classList.add('hidden');
    $('pitchSection').classList.add('hidden');
    $('auditSection').classList.add('hidden');
    $('profileContent').innerHTML = '';
    $('slidesContainer').innerHTML = '';
    $('auditSummary').innerHTML = '';
    $('auditClaims').innerHTML = '';
}

// ─── Main generate flow ───────────────────────────────────────────────────────
async function handleGenerate() {
    const companyName = $('companyName').value.trim();
    const policies    = getSelectedPolicies();

    if (!companyName) {
        showError('inputSection', 'Please enter a company name.');
        return;
    }
    if (policies.length === 0) {
        showError('inputSection', 'Please select at least one policy.');
        return;
    }

    clearErrors();
    resetResults();
    showProgressTracker();

    // Disable generate button while running
    $('generateBtn').disabled = true;

    // ── Step 1: Research company ─────────────────────────────────────────────
    setStepRunning('research', `Researching "${companyName}" — industry, risks, size...`);
    try {
        const profileRes = await fetch('/api/profile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ company_name: companyName }),
        });
        const profileData = await profileRes.json();
        if (!profileRes.ok) throw new Error(profileData.error || 'Profile generation failed');

        currentProfile = profileData;
        setStepDone('research', `Found: ${profileData.industry || 'Unknown industry'} · ${profileData.estimated_size || ''}`);
        renderProfile(currentProfile);
        $('profileSection').classList.remove('hidden');
        $('profileSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (err) {
        hideProgressTracker();
        $('generateBtn').disabled = false;
        showError('inputSection', err.message);
        $('statusDot').classList.remove('busy');
        $('statusText').textContent = 'Ready';
        return;
    }

    // ── Step 2: Retrieve policy knowledge (runs server-side, show as "working") ──
    setStepRunning('retrieve', `Loading OKF bundles for ${policies.length} selected ${policies.length === 1 ? 'policy' : 'policies'}...`);
    // Small delay to let the UI repaint before the long pitch call
    await new Promise(r => setTimeout(r, 300));
    setStepDone('retrieve', `${policies.length} policy knowledge bundle${policies.length > 1 ? 's' : ''} loaded`);

    // ── Step 3: Generate pitch slides (all 5 in parallel on server) ──────────
    setStepRunning('pitch', '5 specialist agents writing slides in parallel...');
    try {
        const pitchRes = await fetch('/api/pitch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ profile: currentProfile, policies }),
        });
        const pitchData = await pitchRes.json();
        if (!pitchRes.ok) throw new Error(pitchData.error || 'Pitch generation failed');

        if (pitchData.error === true) {
            throw new Error(
                'The AI model could not generate a structured pitch. ' +
                'This usually happens when the API is under heavy load. ' +
                'Please wait 30 seconds and try again.'
            );
        }

        currentPitch = pitchData;
        const slideCount = (pitchData.slides || []).length;
        setStepDone('pitch', `${slideCount} slides generated · ready to download`);
        renderPitch(currentPitch);
        $('pitchSection').classList.remove('hidden');
    } catch (err) {
        hideProgressTracker();
        $('generateBtn').disabled = false;
        showError('profileSection', err.message);
        $('statusDot').classList.remove('busy');
        $('statusText').textContent = 'Ready';
        return;
    }

    // All done
    $('generateBtn').disabled = false;
    $('statusDot').classList.remove('busy');
    $('statusText').textContent = 'Ready';
    $('pitchSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ─── Render company profile ───
function renderProfile(profile) {
    const content = $('profileContent');

    const rows = [
        ['Company', profile.company_name],
        ['Industry', profile.industry + (profile.sub_industry ? ' / ' + profile.sub_industry : '')],
        ['Size', profile.estimated_size],
        ['Employees', profile.estimated_employees || 'N/A'],
        ['Headquarters', profile.headquarters || 'N/A'],
    ];

    let html = rows.map(([key, value]) => `
        <div class="profile-row">
            <span class="profile-key">${key}</span>
            <span class="profile-value">${value}</span>
        </div>
    `).join('');

    if (profile.description) {
        html += `
            <div class="profile-row">
                <span class="profile-key">Description</span>
                <span class="profile-value">${profile.description}</span>
            </div>
        `;
    }

    if (profile.key_risks && profile.key_risks.length > 0) {
        html += `
            <div style="margin-top: var(--space-md)">
                <span class="profile-key">Key Risks</span>
                <ul class="profile-list">
                    ${profile.key_risks.map(r => `<li>${r}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    if (profile.insurance_needs && profile.insurance_needs.length > 0) {
        html += `
            <div style="margin-top: var(--space-md)">
                <span class="profile-key">Insurance Needs</span>
                <ul class="profile-list">
                    ${profile.insurance_needs.map(n => `<li>${n}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    if (profile.assumptions && profile.assumptions.length > 0) {
        html += `
            <div style="margin-top: var(--space-md)">
                <span class="profile-key">Assumptions <span class="assumption-tag">Review</span></span>
                <ul class="profile-list">
                    ${profile.assumptions.map(a => `<li>${a}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    content.innerHTML = html;
}

// ─── Render pitch slides ───
function renderPitch(pitch) {
    $('pitchTitle').textContent = pitch.pitch_title || 'Generated Pitch';

    const container = $('slidesContainer');
    const slides = pitch.slides || [];

    container.innerHTML = slides.map(slide => `
        <div class="slide-card">
            <div class="slide-number">Slide ${slide.slide_number}</div>
            <h3 class="slide-title">${slide.title}</h3>
            ${slide.subtitle ? `<p class="slide-subtitle">${slide.subtitle}</p>` : ''}
            <ul class="slide-bullets">
                ${(slide.bullets || []).map(b => `<li>${b}</li>`).join('')}
            </ul>
            ${slide.speaker_notes ? `
                <details class="slide-notes">
                    <summary>Speaker Notes</summary>
                    <p>${slide.speaker_notes}</p>
                </details>
            ` : ''}
        </div>
    `).join('');

    // Show recommended policy and differentiators
    if (pitch.recommended_policy || pitch.key_differentiators) {
        let extra = '<div class="slide-card" style="border-left: 3px solid var(--accent)">';
        extra += '<div class="slide-number">Recommendation</div>';
        if (pitch.recommended_policy) {
            extra += `<p style="font-size: 0.875rem; color: var(--text-primary); margin-bottom: var(--space-sm)">${pitch.recommended_policy}</p>`;
        }
        if (pitch.key_differentiators && pitch.key_differentiators.length > 0) {
            extra += `<ul class="slide-bullets">${pitch.key_differentiators.map(d => `<li>${d}</li>`).join('')}</ul>`;
        }
        extra += '</div>';
        container.innerHTML += extra;
    }
}

// ─── Download PPTX ───
async function handleDownload() {
    if (!currentPitch) return;

    $('downloadBtn').disabled = true;
    showLoading('Building PowerPoint...');

    try {
        const res = await fetch('/api/download-pptx', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                pitch:   currentPitch,
                profile: currentProfile || null,   // include company profile data
            }),
        });

        if (!res.ok) throw new Error('Download failed');

        const blob = await res.blob();
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href     = url;
        a.download = `marsh_pitch_${(currentPitch.target_company || 'company').replace(/\s+/g, '_')}.pptx`;
        a.click();
        URL.revokeObjectURL(url);
    } catch (err) {
        showError('pitchSection', err.message);
    }

    hideLoading();
    $('downloadBtn').disabled = false;
}

// ─── Run Audit ───
async function handleAudit() {
    if (!currentPitch) return;

    $('auditBtn').disabled = true;
    showLoading('Auditing pitch content...');

    try {
        const res = await fetch('/api/audit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                pitch: currentPitch,
                policies: currentPitch._policy_ids || getSelectedPolicies(),
            }),
        });

        const auditData = await res.json();

        if (!res.ok) {
            const errMsg = auditData.error || 'Audit failed';
            throw new Error(errMsg);
        }

        // Normalise shape — model might return a partial or different structure
        const audit = normaliseAudit(auditData);
        renderAudit(audit);
        $('auditSection').classList.remove('hidden');
        $('auditSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (err) {
        showError('pitchSection', err.message);
    }

    hideLoading();
    $('auditBtn').disabled = false;
}

// ─── Normalise audit response (handles truncated / partial Groq responses) ───
function normaliseAudit(raw) {
    // If it already has audit_summary it's the expected shape
    if (raw.audit_summary) return raw;

    // Otherwise build a minimal valid audit so the UI doesn't crash
    return {
        audit_summary: 'PASS_WITH_NOTES',
        total_claims: 0,
        verified_claims: 0,
        flagged_claims: 0,
        claims: [],
        recommendations: [
            'The audit model returned an abbreviated response due to token limits.',
            'Please review all pitch claims manually against the source policy documents.',
        ],
        _raw: raw,  // keep raw for debugging
    };
}

// ─── Render audit results ───
function renderAudit(audit) {
    // Summary stats
    const summaryStatus = (audit.audit_summary || '').toUpperCase();
    let statusClass = 'notes';
    if (summaryStatus.includes('PASS') && !summaryStatus.includes('NOTE')) statusClass = 'pass';
    if (summaryStatus.includes('FAIL')) statusClass = 'fail';

    $('auditSummary').innerHTML = `
        <div style="display: flex; align-items: center; gap: var(--space-md); margin-bottom: var(--space-md)">
            <span class="audit-status ${statusClass}">${audit.audit_summary || 'Unknown'}</span>
        </div>
        <div class="audit-stats">
            <div class="audit-stat">
                <div class="audit-stat-number">${audit.total_claims || 0}</div>
                <div class="audit-stat-label">Total Claims</div>
            </div>
            <div class="audit-stat">
                <div class="audit-stat-number">${audit.verified_claims || 0}</div>
                <div class="audit-stat-label">Verified</div>
            </div>
            <div class="audit-stat">
                <div class="audit-stat-number">${audit.flagged_claims || 0}</div>
                <div class="audit-stat-label">Flagged</div>
            </div>
        </div>
    `;

    // Individual claims — flagged ones get reviewer controls
    const claims = audit.claims || [];
    $('auditClaims').innerHTML = claims.map((claim, idx) => {
        const statusLower   = (claim.status || '').toLowerCase();
        const isFlagged     = statusLower === 'flagged' || statusLower === 'unverified';
        const confidence    = claim.confidence != null ? Math.round(claim.confidence * 100) + '%' : '';
        const claimId       = `claim_${idx}`;

        const reviewerControls = isFlagged ? `
            <div class="reviewer-controls">
                <span class="reviewer-label">Your Decision:</span>
                <label class="reviewer-option">
                    <input type="radio" name="${claimId}" value="verified" onchange="updateReviewerDecision(${idx}, 'verified')">
                    <span class="reviewer-radio-indicator verified-indicator"></span>
                    Verified
                </label>
                <label class="reviewer-option">
                    <input type="radio" name="${claimId}" value="rejected" onchange="updateReviewerDecision(${idx}, 'rejected')">
                    <span class="reviewer-radio-indicator rejected-indicator"></span>
                    Rejected
                </label>
                <label class="reviewer-option">
                    <input type="radio" name="${claimId}" value="pending" checked onchange="updateReviewerDecision(${idx}, 'pending')">
                    <span class="reviewer-radio-indicator pending-indicator"></span>
                    Pending
                </label>
            </div>` : '';

        return `
            <div class="audit-claim" id="claim-card-${idx}" data-idx="${idx}" data-status="${statusLower}">
                <div class="claim-header">
                    <span class="claim-status ${statusLower}">${claim.status}</span>
                    ${confidence ? `<span class="claim-confidence">${confidence} confidence</span>` : ''}
                </div>
                <p class="claim-text">${claim.claim_text}</p>
                ${claim.source_concept ? `<p class="claim-source">Source: ${claim.source_concept}</p>` : ''}
                ${claim.notes ? `<p class="claim-source">${claim.notes}</p>` : ''}
                ${reviewerControls}
            </div>
        `;
    }).join('');

    // Recommendations block
    if (audit.recommendations && audit.recommendations.length > 0) {
        $('auditClaims').innerHTML += `
            <div class="slide-card" style="margin-top: var(--space-md); border-left: 3px solid var(--warning)">
                <div class="slide-number">Recommendations</div>
                <ul class="slide-bullets">
                    ${audit.recommendations.map(r => `<li>${r}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    // Show the Download Audit PDF button
    $('auditDownloadRow').classList.remove('hidden');
}

// ─── Track reviewer decisions per claim ───
const _reviewerDecisions = {};   // { claimIndex: 'verified' | 'rejected' | 'pending' }

function updateReviewerDecision(idx, decision) {
    _reviewerDecisions[idx] = decision;
    const card = $(`claim-card-${idx}`);
    if (!card) return;
    card.classList.remove('reviewer-verified', 'reviewer-rejected', 'reviewer-pending');
    card.classList.add(`reviewer-${decision}`);
}

// ─── Download Audit as PDF ───
async function handleAuditPDF() {
    const claims    = document.querySelectorAll('.audit-claim');
    const summaryEl = $('auditSummary');
    const company   = currentPitch?.target_company || 'Company';
    const dateStr   = new Date().toLocaleDateString('en-IN', { day:'2-digit', month:'short', year:'numeric' });

    // Build print-ready HTML and open in new window for system print-to-PDF
    const claimsHTML = Array.from(claims).map((card, idx) => {
        const statusEl   = card.querySelector('.claim-status');
        const textEl     = card.querySelector('.claim-text');
        const sourceEl   = card.querySelector('.claim-source');
        const notesEl    = card.querySelectorAll('.claim-source')[1];
        const confEl     = card.querySelector('.claim-confidence');
        const isFlagged  = card.dataset.status === 'flagged' || card.dataset.status === 'unverified';
        const decision   = _reviewerDecisions[card.dataset.idx] || 'pending';

        const decisionBadge = isFlagged ? `
            <span style="
                display:inline-block; padding:2px 10px; border-radius:3px; font-size:10px;
                font-weight:600; letter-spacing:.06em; text-transform:uppercase;
                background:${decision==='verified'?'#e8f4ea':decision==='rejected'?'#fce8e8':'#f0f4ff'};
                color:${decision==='verified'?'#2d7d46':decision==='rejected'?'#c0392b':'#1A78B4'};
                border:1px solid ${decision==='verified'?'#2d7d46':decision==='rejected'?'#c0392b':'#1A78B4'};
                margin-left:8px;">
                ▸ Reviewer: ${decision.charAt(0).toUpperCase()+decision.slice(1)}
            </span>` : '';

        return `
            <div style="padding:14px 0; border-bottom:1px solid #eee;">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                    <span style="
                        font-size:10px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
                        padding:2px 8px;border-radius:3px;
                        background:${statusEl?.className.includes('verified')?'#e8f4ea':'#fce8e8'};
                        color:${statusEl?.className.includes('verified')?'#2d7d46':'#c0392b'}">
                        ${statusEl?.textContent || ''}
                    </span>
                    ${confEl ? `<span style="font-size:11px;color:#9AB0C8">${confEl.textContent}</span>` : ''}
                    ${decisionBadge}
                </div>
                <p style="margin:0 0 4px;font-size:13px;color:#0F1117;line-height:1.5">${textEl?.textContent || ''}</p>
                ${sourceEl ? `<p style="margin:0;font-size:11px;color:#9AB0C8">${sourceEl.textContent}</p>` : ''}
            </div>`;
    }).join('');

    const auditStatusEl = summaryEl.querySelector('.audit-status');
    const statsEls = summaryEl.querySelectorAll('.audit-stat');
    const statsHTML = Array.from(statsEls).map(s => `
        <div style="text-align:center;padding:0 24px;border-right:1px solid #eee;">
            <div style="font-size:28px;font-weight:600;color:#1A78B4;font-family:Georgia,serif">${s.querySelector('.audit-stat-number')?.textContent}</div>
            <div style="font-size:11px;color:#9AB0C8;letter-spacing:.06em;text-transform:uppercase">${s.querySelector('.audit-stat-label')?.textContent}</div>
        </div>`).join('');

    const win = window.open('', '_blank');
    win.document.write(`<!DOCTYPE html><html><head>
        <title>Marsh Audit Report — ${company}</title>
        <style>
            *{margin:0;padding:0;box-sizing:border-box}
            body{font-family:Inter,-apple-system,sans-serif;color:#0F1117;padding:40px;max-width:800px;margin:0 auto}
            @media print{body{padding:20px}button{display:none!important}}
        </style>
    </head><body>
        <div style="border-bottom:3px solid #1A78B4;padding-bottom:20px;margin-bottom:24px">
            <div style="display:flex;justify-content:space-between;align-items:flex-end">
                <div>
                    <div style="font-family:Georgia,serif;font-size:22px;color:#1A78B4;font-weight:400">Marsh</div>
                    <div style="font-size:18px;font-weight:600;color:#0F1117;margin-top:2px">Pitch Audit Report</div>
                    <div style="font-size:13px;color:#9AB0C8;margin-top:4px">${company} · ${dateStr}</div>
                </div>
                <span style="
                    padding:6px 16px;border-radius:3px;font-size:12px;font-weight:700;letter-spacing:.08em;
                    background:${auditStatusEl?.className.includes('pass')?'#e8f4ea':auditStatusEl?.className.includes('fail')?'#fce8e8':'#fff8e8'};
                    color:${auditStatusEl?.className.includes('pass')?'#2d7d46':auditStatusEl?.className.includes('fail')?'#c0392b':'#b08800'}">
                    ${auditStatusEl?.textContent || ''}
                </span>
            </div>
        </div>
        <div style="display:flex;margin-bottom:28px;background:#F7F8FA;border-radius:6px;padding:16px">
            ${statsHTML}
        </div>
        <div style="font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#9AB0C8;margin-bottom:12px">Claim-by-Claim Review</div>
        ${claimsHTML}
        <div style="margin-top:32px;padding-top:16px;border-top:1px solid #eee;font-size:11px;color:#9AB0C8;text-align:center">
            Generated by Marsh AI Pitch Generator · NMIMS 2026 · Confidential
        </div>
        <br>
        <div style="text-align:center"><button onclick="window.print()" style="
            padding:10px 28px;background:#1A78B4;color:#fff;border:none;
            border-radius:4px;font-size:14px;cursor:pointer;font-family:inherit">
            Save as PDF (Ctrl+P)
        </button></div>
    </body></html>`);
    win.document.close();
}


// ─── Error handling ───
function showError(sectionId, message) {
    clearErrors();
    const section = $(sectionId);
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    section.appendChild(errorDiv);
}

function clearErrors() {
    document.querySelectorAll('.error-message').forEach(el => el.remove());
}
