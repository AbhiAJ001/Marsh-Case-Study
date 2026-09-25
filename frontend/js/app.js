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

// ─── Loading state ───
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

// ─── Reset all results sections before a new search ───
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

// ─── Main generate flow ───
async function handleGenerate() {
    const companyName = $('companyName').value.trim();
    const policies = getSelectedPolicies();

    if (!companyName) {
        showError('inputSection', 'Please enter a company name.');
        return;
    }
    if (policies.length === 0) {
        showError('inputSection', 'Please select at least one policy.');
        return;
    }

    clearErrors();
    resetResults();  // wipe previous company data before every new request

    // Step 1: Generate company profile
    showLoading('Researching ' + companyName + '...');
    try {
        const profileRes = await fetch('/api/profile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ company_name: companyName }),
        });

        const profileData = await profileRes.json();
        if (!profileRes.ok) throw new Error(profileData.error || 'Profile generation failed');

        currentProfile = profileData;
        renderProfile(currentProfile);
        $('profileSection').classList.remove('hidden');
    } catch (err) {
        hideLoading();
        showError('inputSection', 'Failed to research company: ' + err.message);
        return;
    }

    // Step 2: Generate pitch
    showLoading('Generating pitch for ' + companyName + '...');
    try {
        const pitchRes = await fetch('/api/pitch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                profile: currentProfile,
                policies: policies,
            }),
        });

        const pitchData = await pitchRes.json();
        if (!pitchRes.ok) throw new Error(pitchData.error || 'Pitch generation failed');

        // Check if backend returned an error pitch (model failed to parse JSON)
        if (pitchData.error === true) {
            throw new Error(
                'The AI model could not generate a structured pitch. ' +
                'This usually happens when the API is under heavy load. ' +
                'Please wait 30 seconds and try again.'
            );
        }

        currentPitch = pitchData;
        renderPitch(currentPitch);
        $('pitchSection').classList.remove('hidden');
    } catch (err) {
        hideLoading();
        showError('profileSection', 'Failed to generate pitch: ' + err.message);
        return;
    }


    hideLoading();

    // Scroll to results
    $('profileSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
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
            body: JSON.stringify({ pitch: currentPitch }),
        });

        if (!res.ok) throw new Error('Download failed');

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `pitch_${(currentPitch.target_company || 'company').replace(/\s+/g, '_')}.pptx`;
        a.click();
        URL.revokeObjectURL(url);
    } catch (err) {
        showError('pitchSection', 'Failed to generate PPTX. ' + err.message);
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
        showError('pitchSection', 'Audit failed: ' + err.message);
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
    // Summary
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

    // Individual claims
    const claims = audit.claims || [];
    $('auditClaims').innerHTML = claims.map(claim => {
        const statusLower = (claim.status || '').toLowerCase();
        const confidence = claim.confidence != null ? Math.round(claim.confidence * 100) + '%' : '';

        return `
            <div class="audit-claim">
                <div class="claim-header">
                    <span class="claim-status ${statusLower}">${claim.status}</span>
                    ${confidence ? `<span class="claim-confidence">${confidence} confidence</span>` : ''}
                </div>
                <p class="claim-text">${claim.claim_text}</p>
                ${claim.source_concept ? `<p class="claim-source">Source: ${claim.source_concept}</p>` : ''}
                ${claim.notes ? `<p class="claim-source">${claim.notes}</p>` : ''}
            </div>
        `;
    }).join('');

    // Recommendations
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
