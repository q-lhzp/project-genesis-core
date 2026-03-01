/**
 * Initialization Wizard Logic (v1.0)
 * Handles the 5-step onboarding flow for Genesis Core.
 */

class GenesisSetup {
    constructor() {
        this.currentStep = 1;
        this.totalSteps = 5;
        this.overlay = document.getElementById('wizardOverlay');
        this.nextBtn = document.getElementById('wizardNext');
        this.prevBtn = document.getElementById('wizardPrev');
        this.bridgeList = document.getElementById('bridgeList');

        if (!this.overlay) return;
        this.init();
    }

    async init() {
        this.nextBtn.addEventListener('click', () => this.handleNext());
        this.prevBtn.addEventListener('click', () => this.handlePrev());

        // Check if wizard is needed
        const resp = await fetch('/v1/setup/status');
        const status = await resp.json();
        if (!status.complete) {
            this.overlay.classList.add('active');
            this.loadStep(1);
        }
    }

    async loadStep(step) {
        this.currentStep = step;

        // Update progress UI
        document.querySelectorAll('.wizard-step').forEach(el => {
            const s = parseInt(el.dataset.step);
            el.classList.toggle('active', s === step);
            el.classList.toggle('done', s < step);
        });

        // Update Views
        document.querySelector('.wizard-step-view.active')?.classList.remove('active');
        const view = document.querySelector(`.wizard-step-view[data-step="${step}"]`);
        if (view) view.classList.add('active');

        // Button visibility
        this.prevBtn.style.visibility = step === 1 ? 'hidden' : 'visible';
        this.nextBtn.textContent = step === this.totalSteps ? 'Finalize ✓' : 'Next →';

        // Step-specific logic
        if (step === 1) this.checkHealth();
    }

    async handleNext() {
        if (this.currentStep === this.totalSteps) {
            await this.completeSetup();
        } else {
            this.loadStep(this.currentStep + 1);
        }
    }

    handlePrev() {
        if (this.currentStep > 1) this.loadStep(this.currentStep - 1);
    }

    async checkHealth() {
        this.bridgeList.innerHTML = '<div class="mono" style="color:var(--text-dim);">Scanning system...</div>';
        try {
            const resp = await fetch('/v1/setup/health');
            const data = await resp.json();

            this.bridgeList.innerHTML = data.checks.map(c => `
        <div class="wizard-bridge-item">
          <span>${c.name}</span>
          <span style="color: ${c.success ? '#50c878' : '#e05050'}">${c.status}</span>
        </div>
      `).join('');
        } catch (e) {
            this.bridgeList.innerHTML = '<div class="mono" style="color:#e05050;">Health check failed.</div>';
        }
    }

    async completeSetup() {
        this.nextBtn.disabled = true;
        this.nextBtn.textContent = 'Initializing...';

        await fetch('/v1/setup/complete', { method: 'POST' });

        setTimeout(() => {
            this.overlay.classList.remove('active');
            location.reload(); // Refresh to start core
        }, 1500);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.genesisSetup = new GenesisSetup();
});
