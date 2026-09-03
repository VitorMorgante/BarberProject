/**
 * Barber Heitor - Master Frontend Interactive Logic
 * Handles booking wizard, navbar scrolls, phone masking, and clipboard utilities.
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Navbar Scroll State & Mobile Handling
  const navbar = document.querySelector('.navbar-custom, .custom-navbar, #main-nav');
  const navLinks = document.querySelectorAll('.nav-link, .nav-link-custom');

  if (navbar) {
    const handleScroll = () => {
      if (window.scrollY > 40) {
        navbar.classList.add('scrolled');
        navbar.style.boxShadow = '0 6px 20px rgba(0, 0, 0, 0.6)';
        navbar.style.backgroundColor = 'rgba(6, 8, 13, 0.98)';
      } else {
        navbar.classList.remove('scrolled');
        navbar.style.boxShadow = 'none';
        navbar.style.backgroundColor = 'rgba(6, 8, 13, 0.94)';
      }
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();
  }

  // Smooth scroll for anchor navigation
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
      const targetId = anchor.getAttribute('href');
      if (targetId && targetId !== '#') {
        const targetElement = document.querySelector(targetId);
        if (targetElement) {
          e.preventDefault();
          const offsetTop = targetElement.getBoundingClientRect().top + window.pageYOffset - 80;
          window.scrollTo({
            top: offsetTop,
            behavior: 'smooth'
          });
        }
      }
    });
  });

  // 2. Gallery Category Dynamic Filters
  const filterButtons = document.querySelectorAll('.gallery-filter-btn');
  const galleryCols = document.querySelectorAll('.gallery-col');

  if (filterButtons.length > 0 && galleryCols.length > 0) {
    filterButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        filterButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        const filterValue = btn.getAttribute('data-filter');

        galleryCols.forEach(col => {
          if (filterValue === 'all' || col.getAttribute('data-category') === filterValue || col.getAttribute('data-category')?.includes(filterValue)) {
            col.style.display = 'block';
            col.style.opacity = '1';
          } else {
            col.style.display = 'none';
            col.style.opacity = '0';
          }
        });
      });
    });
  }

  // 3. BOOKING WIZARD (agendamento.html)
  const idServicoInput = document.getElementById('id_servico');
  const idBarbeiroInput = document.getElementById('id_barbeiro');
  const idDataInput = document.getElementById('id_data');
  const idHorarioInput = document.getElementById('id_horario');
  const idNomeInput = document.getElementById('id_nome');
  const idTelefoneInput = document.getElementById('id_telefone');
  const idEmailInput = document.getElementById('id_email');
  const idObservacoesInput = document.getElementById('id_observacoes');

  const timeStepCard = document.getElementById('time-step-card');
  const timeSlotsContainer = document.getElementById('time-slots-container');
  const confirmBtn = document.getElementById('btn-confirm-appointment');

  if (idServicoInput && idBarbeiroInput && idDataInput) {
    const bookingState = {
      serviceId: '',
      serviceName: '',
      servicePrice: 0,
      serviceDuration: '',
      barberId: '',
      barberName: '',
      date: '',
      time: '',
      customer: {
        name: '',
        phone: '',
        email: '',
        notes: ''
      }
    };

    // Minimum date: today
    const now = new Date();
    const yyyy = now.getFullYear();
    const mm = String(now.getMonth() + 1).padStart(2, '0');
    const dd = String(now.getDate()).padStart(2, '0');
    idDataInput.min = `${yyyy}-${mm}-${dd}`;

    const updateSummary = () => {
      const sumService = document.getElementById('sum-service-val');
      const sumBarber = document.getElementById('sum-barber-val');
      const sumDate = document.getElementById('sum-date-val');
      const sumTime = document.getElementById('sum-time-val');
      const sumClient = document.getElementById('sum-client-val');
      const sumPhone = document.getElementById('sum-phone-val');
      const sumDuration = document.getElementById('sum-duration-val');
      const sumTotalPrice = document.getElementById('sum-total-price');

      if (sumService) sumService.textContent = bookingState.serviceName || 'Não selecionado';
      if (sumBarber) sumBarber.textContent = bookingState.barberName || 'Não selecionado';
      if (sumDuration) sumDuration.textContent = bookingState.serviceDuration || 'Não selecionada';

      if (sumDate) {
        if (bookingState.date) {
          const parts = bookingState.date.split('-');
          sumDate.textContent = parts.length === 3 ? `${parts[2]}/${parts[1]}/${parts[0]}` : bookingState.date;
        } else {
          sumDate.textContent = 'Não selecionada';
        }
      }

      if (sumTime) sumTime.textContent = bookingState.time || 'Não selecionado';
      if (sumClient) sumClient.textContent = bookingState.customer.name || 'Não informado';
      if (sumPhone) sumPhone.textContent = bookingState.customer.phone || 'Não informado';

      if (sumTotalPrice) {
        sumTotalPrice.textContent = bookingState.servicePrice
          ? `R$ ${bookingState.servicePrice.toFixed(2).replace('.', ',')}`
          : 'R$ 0,00';
      }

      if (confirmBtn) {
        const isValid = bookingState.serviceId &&
                        bookingState.barberId &&
                        bookingState.date &&
                        bookingState.time &&
                        bookingState.customer.name &&
                        bookingState.customer.phone &&
                        /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(bookingState.customer.email);
        confirmBtn.disabled = !isValid;
      }
    };

    const selectService = (id, name, price, duration) => {
      bookingState.serviceId = id;
      bookingState.serviceName = name;
      bookingState.servicePrice = parseFloat(price) || 0;
      bookingState.serviceDuration = duration;
      idServicoInput.value = id;

      document.querySelectorAll('.service-select-item').forEach(el => {
        if (el.getAttribute('data-service-id') === String(id)) {
          el.classList.add('selected');
        } else {
          el.classList.remove('selected');
        }
      });
      updateSummary();
    };

    document.querySelectorAll('.service-select-item').forEach(el => {
      el.addEventListener('click', () => {
        const id = el.getAttribute('data-service-id');
        const name = el.getAttribute('data-service-name');
        const price = el.getAttribute('data-service-price');
        const dur = el.getAttribute('data-service-duration');
        selectService(id, name, price, dur);
      });
    });

    const selectBarber = (id, name) => {
      bookingState.barberId = id;
      bookingState.barberName = name;
      idBarbeiroInput.value = id;

      document.querySelectorAll('.barber-select-item').forEach(el => {
        if (el.getAttribute('data-barber-id') === String(id)) {
          el.classList.add('selected');
        } else {
          el.classList.remove('selected');
        }
      });
      updateSummary();
      loadAvailableTimes();
    };

    document.querySelectorAll('.barber-select-item').forEach(el => {
      el.addEventListener('click', () => {
        const id = el.getAttribute('data-barber-id');
        const name = el.getAttribute('data-barber-name');
        selectBarber(id, name);
      });
    });

    const loadAvailableTimes = () => {
      const barberId = idBarbeiroInput.value;
      const dateVal = idDataInput.value;

      if (!barberId || !dateVal) {
        if (timeStepCard) timeStepCard.classList.add('d-none');
        return;
      }

      if (timeStepCard) timeStepCard.classList.remove('d-none');
      if (timeSlotsContainer) {
        timeSlotsContainer.innerHTML = '<p class="text-secondary py-3 w-100 text-center small"><i class="bi bi-arrow-repeat spin me-2"></i>Consultando horários disponíveis...</p>';
      }

      fetch(`/api/horarios-disponiveis/?barbeiro_id=${barberId}&data=${dateVal}`)
        .then(res => res.json())
        .then(data => {
          if (!timeSlotsContainer) return;
          timeSlotsContainer.innerHTML = '';
          if (data.horarios && data.horarios.length > 0) {
            data.horarios.forEach(slot => {
              const btn = document.createElement('button');
              btn.type = 'button';
              btn.className = 'time-slot-btn';
              btn.textContent = slot.horario;

              if (!slot.disponivel) {
                btn.disabled = true;
              } else {
                if (idHorarioInput.value === slot.horario) {
                  btn.classList.add('selected');
                  bookingState.time = slot.horario;
                }
                btn.addEventListener('click', () => {
                  document.querySelectorAll('.time-slot-btn').forEach(b => b.classList.remove('selected'));
                  btn.classList.add('selected');
                  idHorarioInput.value = slot.horario;
                  bookingState.time = slot.horario;
                  updateSummary();
                });
              }
              timeSlotsContainer.appendChild(btn);
            });
          } else {
            timeSlotsContainer.innerHTML = '<p class="text-secondary py-3 w-100 text-center small">Nenhum horário livre nesta data. Tente outro dia.</p>';
          }
          updateSummary();
        })
        .catch(err => {
          if (timeSlotsContainer) {
            timeSlotsContainer.innerHTML = '<p class="text-danger py-3 w-100 text-center small">Erro ao carregar horários. Tente novamente.</p>';
          }
        });
    };

    idDataInput.addEventListener('change', (e) => {
      bookingState.date = e.target.value;
      updateSummary();
      loadAvailableTimes();
    });

    const updateCustomerFields = () => {
      if (idNomeInput) bookingState.customer.name = idNomeInput.value.trim();
      if (idTelefoneInput) bookingState.customer.phone = idTelefoneInput.value.trim();
      if (idEmailInput) bookingState.customer.email = idEmailInput.value.trim();
      if (idObservacoesInput) bookingState.customer.notes = idObservacoesInput.value.trim();
      updateSummary();
    };

    [idNomeInput, idTelefoneInput, idEmailInput, idObservacoesInput].forEach(inp => {
      if (inp) inp.addEventListener('input', updateCustomerFields);
    });

    // Handle initial values (URL params or recovery from POST)
    const urlParams = new URLSearchParams(window.location.search);
    const paramService = urlParams.get('servico') || idServicoInput.value;
    const paramBarber = urlParams.get('barbeiro') || idBarbeiroInput.value;

    if (paramService) {
      const sEl = document.querySelector(`.service-select-item[data-service-id="${paramService}"]`);
      if (sEl) {
        selectService(
          paramService,
          sEl.getAttribute('data-service-name'),
          sEl.getAttribute('data-service-price'),
          sEl.getAttribute('data-service-duration')
        );
      }
    }

    if (paramBarber) {
      const bEl = document.querySelector(`.barber-select-item[data-barber-id="${paramBarber}"]`);
      if (bEl) {
        selectBarber(paramBarber, bEl.getAttribute('data-barber-name'));
      }
    }

    if (idDataInput.value) {
      bookingState.date = idDataInput.value;
      loadAvailableTimes();
    }

    updateCustomerFields();
  }

  // 4. Phone Input Mask (XX) XXXXX-XXXX
  const applyPhoneMask = (input) => {
    if (!input) return;
    const format = (val) => {
      let v = val.replace(/\D/g, '');
      if (v.length > 11) v = v.slice(0, 11);
      if (v.length > 10) return `(${v.slice(0, 2)}) ${v.slice(2, 7)}-${v.slice(7)}`;
      if (v.length > 6) return `(${v.slice(0, 2)}) ${v.slice(2, 6)}-${v.slice(6)}`;
      if (v.length > 2) return `(${v.slice(0, 2)}) ${v.slice(2)}`;
      if (v.length > 0) return `(${v}`;
      return '';
    };

    if (input.value) input.value = format(input.value);
    input.addEventListener('input', (e) => {
      e.target.value = format(e.target.value);
    });
  };

  document.querySelectorAll('input[type="tel"], input[name="telefone"], #id_telefone').forEach(applyPhoneMask);
});

// Global Clipboard Utility
window.copyPixCode = function(inputId, buttonId, feedbackId) {
  const input = document.getElementById(inputId);
  const btn = document.getElementById(buttonId);
  const feedback = document.getElementById(feedbackId);

  if (!input) return;
  input.select();
  navigator.clipboard.writeText(input.value).then(() => {
    if (btn) {
      const orig = btn.innerHTML;
      btn.innerHTML = '<i class="bi bi-check-lg me-1"></i> Copiado!';
      btn.classList.add('btn-success');
      btn.classList.remove('btn-brand');
      setTimeout(() => {
        btn.innerHTML = orig;
        btn.classList.remove('btn-success');
        btn.classList.add('btn-brand');
      }, 3000);
    }
    if (feedback) {
      feedback.classList.remove('d-none');
      setTimeout(() => feedback.classList.add('d-none'), 3500);
    }
  }).catch(() => {
    alert("Código copiado: " + input.value);
  });
};
