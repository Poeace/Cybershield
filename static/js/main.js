// ==========================================================================
// CyberShield frontend JS
// All original functionality preserved; new additions (PWA registration,
// bottom-nav behavior, install prompt, connection badge) are clearly marked.
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
  // ===== ORIGINAL: AOS init =====
  if (window.AOS) {
    window.AOS.init({ duration: 800, once: true });
  }

  // ===== ORIGINAL: Particle init (no-op kept for compatibility) =====
  try {
    if (window.particlesJS) {
      // particlesJS already initialized in particles-config.js (optional)
    } else {
      // no-op
    }
  } catch (e) {}

  // ===== ORIGINAL: Animate counters (data-counter attribute) =====
  const els = document.querySelectorAll('[data-counter]');
  els.forEach((el) => {
    const target = Number(el.getAttribute('data-counter') || '0');
    const speed = Number(el.getAttribute('data-speed') || '900');
    const format = el.getAttribute('data-format') || '';

    const animate = () => {
      const start = performance.now();
      const step = (now) => {
        const t = Math.min(1, (now - start) / speed);
        const val = Math.floor(target * t);
        if (format === 'comma') {
          el.textContent = val.toLocaleString();
        } else {
          el.textContent = String(val);
        }
        if (t < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    };

    const io = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          io.disconnect();
          animate();
        }
      },
      { threshold: 0.25 }
    );
    io.observe(el);
  });

  // ===== ORIGINAL: BACKUP & RANSOMWARE RECOVERY STATS LOADER =====
  const statsContainer = document.getElementById('ransomware-stats');
  if (statsContainer) {
    fetch('/api/ransomware/stats')
      .then(res => res.json())
      .then(data => {
        const fields = [
          { id: 'protected-files', val: data.protected_files },
          { id: 'backups-created', val: data.backups_created },
          { id: 'files-restored', val: data.files_restored },
          { id: 'threats-detected', val: data.threats_detected },
          { id: 'recovery-rate', val: data.recovery_success_rate, suffix: '%' },
        ];
        fields.forEach(f => {
          const el = document.getElementById(f.id);
          if (el) {
            el.textContent = f.val + (f.suffix || '');
            if (el.hasAttribute('data-counter')) {
              el.setAttribute('data-counter', f.val);
            }
          }
        });
      })
      .catch(err => {
        console.warn('Failed to load backup stats:', err);
      });
  }

  // ===== ORIGINAL: RANSOMWARE SCAN FORM ANIMATION =====
  const scanForm = document.getElementById('scanForm');
  if (scanForm) {
    const scanInput = document.getElementById('scanFileInput');
    const dropZone = document.getElementById('scanDropZone');
    const fileInfo = document.getElementById('scanFileInfo');
    const fileName = document.getElementById('scanFileName');
    const fileSize = document.getElementById('scanFileSize');
    const scanProgress = document.getElementById('scanProgress');
    const scanBtn = document.getElementById('scanBtn');
    const statusEl = document.getElementById('scanStatusText');

    function updateFileInfo(file) {
      if (file) {
        fileName.textContent = file.name;
        const sz = (file.size / 1024).toFixed(1);
        fileSize.textContent = `(${sz} KB)`;
        fileInfo?.classList.remove('d-none');
      } else {
        fileInfo?.classList.add('d-none');
      }
    }

    if (scanInput) {
      scanInput.addEventListener('change', (e) => {
        updateFileInfo(e.target.files[0]);
      });
    }

    if (dropZone) {
      dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--neon)';
        dropZone.style.background = 'rgba(39,215,255,0.08)';
      });
      dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'rgba(39,215,255,0.25)';
        dropZone.style.background = 'transparent';
      });
      dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'rgba(39,215,255,0.25)';
        dropZone.style.background = 'transparent';
        if (e.dataTransfer.files.length > 0 && scanInput) {
          scanInput.files = e.dataTransfer.files;
          updateFileInfo(e.dataTransfer.files[0]);
        }
      });
      dropZone.addEventListener('click', () => {
        scanInput?.click();
      });
    }

    // Scan button animation
    scanForm.addEventListener('submit', () => {
      if (scanProgress) scanProgress.classList.remove('d-none');
      if (scanBtn) {
        scanBtn.disabled = true;
        scanBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i> Scanning...';
      }

      const statusTexts = [
        'Reading file bytes...',
        'Analyzing entropy...',
        'Checking file signatures...',
        'Computing SHA-256 hash...',
        'Checking known ransomware patterns...',
        'Looking up encryption database...',
        'Calculating risk score...',
        'Generating report...',
      ];
      let i = 0;
      const interval = setInterval(() => {
        if (i < statusTexts.length && statusEl) {
          statusEl.textContent = statusTexts[i];
          i++;
        } else {
          clearInterval(interval);
        }
      }, 800);
    });
  }

  // ===== ORIGINAL: DECRYPT BUTTON HANDLER (ENHANCED) =====
  document.querySelectorAll('.decrypt-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      const scanId = this.dataset.scanId;
      const resultDiv = document.getElementById('decryptResult-' + scanId);
      const originalText = this.innerHTML;
      const decryptSection = this.closest('.decrypt-section') || resultDiv;

      // Show progress
      this.disabled = true;
      this.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i> Decrypting...';

      // Show progress bar
      let progressHtml = `
        <div class="decrypt-progress mb-3" id="decryptProgress-${scanId}">
          <div class="progress-track">
            <div class="progress-fill" id="progressFill-${scanId}"></div>
          </div>
          <div class="progress-status" id="progressStatus-${scanId}">
            <i class="fa-solid fa-spinner fa-spin me-1"></i> Initializing decryption...
          </div>
        </div>
      `;
      if (resultDiv) {
        resultDiv.innerHTML = progressHtml;
      }

      // Animate progress
      let progressInterval = setInterval(() => {
        const fill = document.getElementById('progressFill-' + scanId);
        const status = document.getElementById('progressStatus-' + scanId);
        if (fill) {
          const current = parseFloat(fill.style.width) || 0;
          if (current < 80) {
            const increment = Math.random() * 15 + 5;
            fill.style.width = Math.min(current + increment, 80) + '%';
          }
        }
        if (status) {
          const texts = [
            'Initializing decryption...',
            'Retrieving encryption key from secure database...',
            'Decrypting file data (AES-256)...',
            'Verifying decryption integrity...',
            'Saving recovered file...',
          ];
          const idx = Math.floor(Math.random() * texts.length);
          status.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i> ' + texts[idx];
        }
      }, 1200);

      fetch('/module/ransomware/decrypt/' + scanId, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      })
        .then(res => res.json())
        .then(data => {
          clearInterval(progressInterval);

          // Set progress to 100% on completion
          const fill = document.getElementById('progressFill-' + scanId);
          if (fill) fill.style.width = '100%';

          if (data.success) {
            const status = document.getElementById('progressStatus-' + scanId);
            if (status) {
              status.innerHTML = '<i class="fa-solid fa-check-circle" style="color: var(--safe);"></i> Decryption complete!';
            }

            // Build open button HTML (only for supported types)
            let openBtnHtml = '';
            if (data.open_url) {
              openBtnHtml = `
                <a href="${data.open_url}" target="_blank" class="btn btn-open-file">
                  <i class="fa-solid fa-eye me-1"></i> Open File
                </a>
              `;
            }

            // Build success card
            setTimeout(() => {
              if (resultDiv) {
                resultDiv.innerHTML = `
                  <div class="decrypt-success-card">
                    <div class="d-flex align-items-center gap-3 mb-3">
                      <div class="success-icon">
                        <i class="fa-solid fa-check-circle"></i>
                      </div>
                      <div>
                        <div class="success-title">File decrypted successfully.</div>
                        <div class="small" style="color: var(--safe); opacity: 0.7;">
                          <i class="fa-solid fa-clock me-1"></i> ${data.decryption_timestamp}
                        </div>
                      </div>
                    </div>

                    <div class="recovery-badge mb-3">
                      <i class="fa-solid fa-shield-check"></i> Recovery Status: ${data.recovery_status.toUpperCase()}
                    </div>

                    <table class="file-details-table">
                      <tr>
                        <td><i class="fa-solid fa-file me-1"></i> Original Filename</td>
                        <td><strong>${data.original_filename}</strong></td>
                      </tr>
                      <tr>
                        <td><i class="fa-solid fa-weight me-1"></i> File Size</td>
                        <td><strong>${data.file_size_display || (data.file_size + ' bytes')}</strong></td>
                      </tr>
                      <tr>
                        <td><i class="fa-solid fa-calendar me-1"></i> Decryption Date & Time</td>
                        <td><strong>${data.decryption_timestamp}</strong></td>
                      </tr>
                      <tr>
                        <td><i class="fa-solid fa-shield-check me-1"></i> Recovery Status</td>
                        <td><span class="recovery-badge"><i class="fa-solid fa-check-circle"></i> ${data.recovery_status.toUpperCase()}</span></td>
                      </tr>
                    </table>

                    <div class="mt-3 decrypt-action-buttons">
                      <a href="${data.download_url}" class="btn btn-download">
                        <i class="fa-solid fa-download me-1"></i> Download Decrypted File
                      </a>
                      ${openBtnHtml}
                    </div>
                  </div>
                `;
              }

              // Update button state
              this.innerHTML = '<i class="fa-solid fa-check me-1"></i> Decrypted';
              this.classList.remove('cyber-btn');
              this.classList.add('btn', 'btn-outline-success');
            }, 600);
          } else {
            // Failure - show error card with categorized reason
            setTimeout(() => {
              if (resultDiv) {
                resultDiv.innerHTML = `
                  <div class="decrypt-error-card">
                    <div class="d-flex align-items-center gap-3 mb-3">
                      <div class="error-icon">
                        <i class="fa-solid fa-circle-exclamation"></i>
                      </div>
                      <div>
                        <div class="error-title">${data.message || 'Decryption is not possible.'}</div>
                      </div>
                    </div>

                    <div class="error-category mb-3">
                      <i class="fa-solid fa-triangle-exclamation"></i> ${data.error || 'Unknown Error'}
                    </div>

                    <div class="error-details">
                      ${data.error_details || 'No additional details available.'}
                    </div>
                  </div>

                  <!-- Security Recommendations -->
                  <div class="decrypt-recommendations-card mt-3">
                    <div class="rec-title">
                      <i class="fa-solid fa-shield me-1"></i> Security Recommendations
                    </div>
                    <ul class="rec-list">
                      <li>Restore the file from a clean backup if available.</li>
                      <li>Disconnect the infected device from the network immediately.</li>
                      <li>Do not pay the ransom — paying does not guarantee file recovery.</li>
                      <li>Scan the system with trusted antivirus/anti-malware software.</li>
                      <li>Update the operating system and security software to the latest versions.</li>
                      <li>Report the incident to the Cyber Crime authorities if ransomware infection is suspected.</li>
                      <li>Contact a cybersecurity professional if important data is affected.</li>
                    </ul>
                  </div>
                `;
              }

              // Reset button
              this.disabled = false;
              this.innerHTML = '<i class="fa-solid fa-key me-1"></i> Retry Decryption';
            }, 600);
          }

          // Hide progress after delay
          setTimeout(() => {
            const progEl = document.getElementById('decryptProgress-' + scanId);
            if (progEl) progEl.style.display = 'none';
          }, 2000);
        })
        .catch(() => {
          clearInterval(progressInterval);

          setTimeout(() => {
            if (resultDiv) {
              resultDiv.innerHTML = `
                <div class="decrypt-error-card">
                  <div class="d-flex align-items-center gap-3 mb-3">
                    <div class="error-icon">
                      <i class="fa-solid fa-circle-exclamation"></i>
                    </div>
                    <div>
                      <div class="error-title">Decryption request failed.</div>
                    </div>
                  </div>

                  <div class="error-category mb-3">
                    <i class="fa-solid fa-triangle-exclamation"></i> Network / Server Error
                  </div>

                  <div class="error-details">
                    The decryption request could not be completed due to a network or server error.
                    Please check your connection and try again. If the problem persists, contact support.
                  </div>
                </div>

                <!-- Security Recommendations -->
                <div class="decrypt-recommendations-card mt-3">
                  <div class="rec-title">
                    <i class="fa-solid fa-shield me-1"></i> Security Recommendations
                  </div>
                  <ul class="rec-list">
                    <li>Restore the file from a clean backup if available.</li>
                    <li>Disconnect the infected device from the network immediately.</li>
                    <li>Do not pay the ransom — paying does not guarantee file recovery.</li>
                    <li>Scan the system with trusted antivirus/anti-malware software.</li>
                    <li>Update the operating system and security software to the latest versions.</li>
                    <li>Report the incident to the Cyber Crime authorities if ransomware infection is suspected.</li>
                    <li>Contact a cybersecurity professional if important data is affected.</li>
                  </ul>
                </div>
              `;
            }
            this.disabled = false;
            this.innerHTML = originalText;
          }, 600);
        });
    });
  });

  // ===== NEW: PASSWORD VISIBILITY TOGGLE =====
  document.querySelectorAll('.password-toggle-btn').forEach(btn => {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      
      // Find the associated password input
      const passwordInput = this.parentElement.querySelector('.password-input');
      if (!passwordInput) return;
      
      // Toggle the input type between password and text
      const isPassword = passwordInput.type === 'password';
      passwordInput.type = isPassword ? 'text' : 'password';
      
      // Update the icon
      const icon = this.querySelector('i');
      if (icon) {
        icon.classList.toggle('fa-eye');
        icon.classList.toggle('fa-eye-slash');
      }
    });
  });

  // ===== ORIGINAL: BREACH CHECK BUTTON HANDLER =====
  const breachCheckBtn = document.getElementById('checkBreachBtn');
  if (breachCheckBtn) {
    // Handler is in cookies.html template directly
  }

  // ===== ORIGINAL: RISK METER ANIMATION =====
  const riskMeterFill = document.querySelector('.risk-meter-fill');
  if (riskMeterFill) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const offset = riskMeterFill.getAttribute('stroke-dashoffset');
            riskMeterFill.style.transition = 'none';
            riskMeterFill.setAttribute('stroke-dashoffset', '326.73');
            riskMeterFill.getBoundingClientRect();
            riskMeterFill.style.transition = 'stroke-dashoffset 1.5s ease';
            requestAnimationFrame(() => {
              riskMeterFill.setAttribute('stroke-dashoffset', offset);
            });
            observer.disconnect();
          }
        });
      },
      { threshold: 0.3 }
    );
    observer.observe(riskMeterFill);
  }

  // ======================================================================
  // NEW: PWA SERVICE WORKER REGISTRATION
  // ======================================================================
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/service-worker.js')
        .then((reg) => {
          console.log('[CyberShield] Service worker registered:', reg.scope);
        })
        .catch((err) => {
          console.warn('[CyberShield] Service worker registration failed:', err);
        });
    });
  }

  // ======================================================================
  // NEW: BEFORE INSTALL PROMPT (PWA install button UI)
  // ======================================================================
  let deferredPrompt = null;
  const installPromptEl = document.getElementById('installPrompt');
  const installBtn = document.getElementById('installPromptBtn');
  const installClose = document.getElementById('installPromptClose');

  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    if (installPromptEl) {
      installPromptEl.classList.remove('d-none');
    }
  });

  if (installBtn) {
    installBtn.addEventListener('click', async () => {
      if (!deferredPrompt) return;
      deferredPrompt.prompt();
      const choice = await deferredPrompt.userChoice;
      if (choice.outcome === 'accepted') {
        console.log('[CyberShield] App installed.');
      }
      deferredPrompt = null;
      if (installPromptEl) installPromptEl.classList.add('d-none');
    });
  }

  if (installClose) {
    installClose.addEventListener('click', () => {
      if (installPromptEl) installPromptEl.classList.add('d-none');
      deferredPrompt = null;
    });
  }

  // Hide install prompt after app is installed
  window.addEventListener('appinstalled', () => {
    if (installPromptEl) installPromptEl.classList.add('d-none');
    deferredPrompt = null;
  });

  // ======================================================================
  // NEW: BOTTOM NAV — hide on keyboard open (mobile), show on scroll up
  // ======================================================================
  const bottomNav = document.querySelector('.bottom-nav');
  if (bottomNav) {
    let lastY = window.scrollY;
    let keyboardOpen = false;

    const maybeHide = () => {
      // Detect virtual keyboard on small screens: if viewport height shrinks
      // substantially, assume keyboard is open and slide the nav away.
      if (window.innerHeight < 400) {
        keyboardOpen = true;
        bottomNav.classList.add('hide-bottom');
      } else if (keyboardOpen) {
        keyboardOpen = false;
        bottomNav.classList.remove('hide-bottom');
      }
    };

    window.addEventListener('resize', maybeHide);

    // Hide on scroll down, show on scroll up (desktop-adjacent behavior)
    window.addEventListener('scroll', () => {
      const y = window.scrollY;
      if (Math.abs(y - lastY) > 40) {
        if (y > lastY && y > 80) {
          bottomNav.classList.add('hide-bottom');
        } else {
          bottomNav.classList.remove('hide-bottom');
        }
        lastY = y;
      }
    }, { passive: true });
  }

  // ======================================================================
  // NEW: ONLINE / OFFLINE CONNECTION BADGE
  // ======================================================================
  const connBadge = document.getElementById('connectionBadge');
  const connText = document.getElementById('connectionBadgeText');

  const updateConnection = () => {
    if (!connBadge || !connText) return;
    if (navigator.onLine) {
      connBadge.classList.add('d-none');
    } else {
      connBadge.classList.remove('d-none');
      connText.textContent = 'You are offline';
    }
  };

  window.addEventListener('online', updateConnection);
  window.addEventListener('offline', updateConnection);
  updateConnection();
});

