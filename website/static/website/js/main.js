/**
 * Delacruz Barber - Premium Interactive Backend Integration Logic
 * Implements smooth scroll, gallery filtering, dynamic booking wizard with Django API interaction.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Initialize state
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

  // 1. Navbar Scroll Class Toggle & Smooth Navigation
  const navbar = document.querySelector('.navbar-custom');
  const navLinks = document.querySelectorAll('.nav-link-custom');
  
  if (navbar) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
      } else {
        navbar.classList.remove('scrolled');
      }
    });
  }

  // Handle active class for navigation matching scroll sections
  const sections = document.querySelectorAll('section');
  window.addEventListener('scroll', () => {
    let current = '';
    const scrollPos = window.scrollY + 150; // offset for nav

    sections.forEach(section => {
      const sectionTop = section.offsetTop;
      const sectionHeight = section.clientHeight;
      if (scrollPos >= sectionTop && scrollPos < sectionTop + sectionHeight) {
        current = section.getAttribute('id');
      }
    });

    navLinks.forEach(link => {
      link.classList.remove('active');
      if (link.getAttribute('href') === `#${current}`) {
        link.classList.add('active');
      }
    });
  });

  // Smooth scroll adjustment for navbar link navigation
  navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      const href = link.getAttribute('href');
      
      // Only handle smooth scroll if it is an anchor on the same page
      if (href.startsWith('#') || (href.includes('#') && window.location.pathname === '/')) {
        e.preventDefault();
        const targetId = href.substring(href.indexOf('#'));
        const targetSection = document.querySelector(targetId);

        if (targetSection) {
          const offsetPosition = targetSection.offsetTop - 85; // navbar offset
          window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
          });
        }
      }
    });
  });

  // Hero custom link buttons
  const heroCTAButtons = document.querySelectorAll('.hero-scroll-btn');
  heroCTAButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      const href = btn.getAttribute('href');
      if (href.startsWith('#')) {
        e.preventDefault();
        const targetSection = document.querySelector(href);
        if (targetSection) {
          const offsetPosition = targetSection.offsetTop - 85;
          window.scrollTo({
            top: offsetPosition,
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
          if (filterValue === 'all' || col.getAttribute('data-category') === filterValue) {
            col.classList.remove('hide');
            col.style.display = 'block';
          } else {
            col.classList.add('hide');
            col.style.display = 'none';
          }
        });
      });
    });
  }

  // ==========================================
  // BOOKING WIZARD INTERACTION (agendamento.html)
  // ==========================================
  
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

  // Verify we are on the booking page
  if (idServicoInput) {
    
    // Set minimal date placeholder as today's date
    const today = new Date();
    const yyyy = today.getFullYear();
    const mm = String(today.getMonth() + 1).padStart(2, '0');
    const dd = String(today.getDate()).padStart(2, '0');
    idDataInput.min = `${yyyy}-${mm}-${dd}`;

    // Select Service helper
    const selectService = (id, name, price, duration) => {
      bookingState.serviceId = id;
      bookingState.serviceName = name;
      bookingState.servicePrice = parseFloat(price);
      bookingState.serviceDuration = duration;

      idServicoInput.value = id;

      document.querySelectorAll('.service-select-item').forEach(item => {
        if (item.getAttribute('data-service-id') === String(id)) {
          item.classList.add('selected');
          const stepCard = item.closest('.step-card');
          if (stepCard) stepCard.classList.add('active');
        } else {
          item.classList.remove('selected');
        }
      });

      updateSummary();
    };

    // Service items click
    document.querySelectorAll('.service-select-item').forEach(item => {
      item.addEventListener('click', () => {
        const id = item.getAttribute('data-service-id');
        const name = item.getAttribute('data-service-name');
        const price = item.getAttribute('data-service-price');
        const duration = item.getAttribute('data-service-duration');
        selectService(id, name, price, duration);
      });
    });

    // Select Barber helper
    const selectBarber = (id, name) => {
      bookingState.barberId = id;
      bookingState.barberName = name;

      idBarbeiroInput.value = id;

      document.querySelectorAll('.barber-select-item').forEach(item => {
        if (item.getAttribute('data-barber-id') === String(id)) {
          item.classList.add('selected');
          const stepCard = item.closest('.step-card');
          if (stepCard) stepCard.classList.add('active');
        } else {
          item.classList.remove('selected');
        }
      });

      updateSummary();
      loadAvailableTimes();
    };

    // Barber items click
    document.querySelectorAll('.barber-select-item').forEach(item => {
      item.addEventListener('click', () => {
        const id = item.getAttribute('data-barber-id');
        const name = item.getAttribute('data-barber-name');
        selectBarber(id, name);
      });
    });

    // Load available time slots from backend API
    const loadAvailableTimes = () => {
      const barberId = idBarbeiroInput.value;
      const dateVal = idDataInput.value;

      if (!barberId || !dateVal) {
        timeStepCard.classList.add('d-none');
        return;
      }

      timeSlotsContainer.innerHTML = '<p class="text-muted-custom py-2 w-100 text-center"><i class="bi bi-arrow-repeat spin me-2"></i>Carregando horários...</p>';
      timeStepCard.classList.remove('d-none');

      fetch(`/api/horarios-disponiveis/?barbeiro_id=${barberId}&data=${dateVal}`)
        .then(response => response.json())
        .then(data => {
          timeSlotsContainer.innerHTML = '';
          if (data.horarios && data.horarios.length > 0) {
            data.horarios.forEach(slot => {
              const btn = document.createElement('button');
              btn.type = 'button'; // Do NOT submit form
              btn.className = 'btn time-btn';
              btn.setAttribute('data-time', slot.horario);
              btn.textContent = slot.horario;

              if (!slot.disponivel) {
                btn.className = 'btn time-btn text-muted';
                btn.disabled = true;
              } else {
                if (idHorarioInput.value === slot.horario) {
                  btn.classList.add('selected');
                  bookingState.time = slot.horario;
                  const stepCard = timeStepCard;
                  if (stepCard) stepCard.classList.add('active');
                }
                btn.addEventListener('click', () => {
                  document.querySelectorAll('.time-btn').forEach(b => b.classList.remove('selected'));
                  btn.classList.add('selected');
                  idHorarioInput.value = slot.horario;
                  bookingState.time = slot.horario;
                  
                  const stepCard = btn.closest('.step-card');
                  if (stepCard) stepCard.classList.add('active');

                  updateSummary();
                });
              }
              timeSlotsContainer.appendChild(btn);
            });
          } else {
            timeSlotsContainer.innerHTML = '<p class="text-muted-custom py-2 w-100 text-center">Nenhum horário disponível para este dia.</p>';
          }
          updateSummary();
        })
        .catch(err => {
          console.error('Error fetching time slots:', err);
          timeSlotsContainer.innerHTML = '<p class="text-danger py-2 w-100 text-center">Erro ao carregar horários. Tente novamente.</p>';
        });
    };

    // Date change listener
    idDataInput.addEventListener('change', (e) => {
      bookingState.date = e.target.value;
      const stepCard = idDataInput.closest('.step-card');
      if (bookingState.date) {
        if (stepCard) stepCard.classList.add('active');
      } else {
        if (stepCard) stepCard.classList.remove('active');
      }
      updateSummary();
      loadAvailableTimes();
    });

    // Customer fields input listeners
    const updateCustomerFields = () => {
      bookingState.customer.name = idNomeInput.value.trim();
      bookingState.customer.phone = idTelefoneInput.value.trim();
      bookingState.customer.email = idEmailInput.value.trim();
      bookingState.customer.notes = idObservacoesInput.value.trim();

      const hasRequired = bookingState.customer.name && bookingState.customer.phone && bookingState.customer.email;
      const stepCard = document.getElementById('customer-step-card');
      if (hasRequired) {
        if (stepCard) stepCard.classList.add('active');
      } else {
        if (stepCard) stepCard.classList.remove('active');
      }
      updateSummary();
    };

    [idNomeInput, idTelefoneInput, idEmailInput, idObservacoesInput].forEach(input => {
      if (input) {
        input.addEventListener('input', updateCustomerFields);
      }
    });

    // Update Summary panel
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
          const dateParts = bookingState.date.split('-');
          if (dateParts.length === 3) {
            sumDate.textContent = `${dateParts[2]}/${dateParts[1]}/${dateParts[0]}`;
          } else {
            sumDate.textContent = bookingState.date;
          }
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

      // Check overall form validity to enable submit
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

    // Pre-populate if fields are already filled (e.g. back from validation error, or using URL parameters)
    const initPreselections = () => {
      // 1. URL Query parameters check
      const urlParams = new URLSearchParams(window.location.search);
      const paramService = urlParams.get('servico');
      const paramBarber = urlParams.get('barbeiro');

      // 2. Check existing form field values (POST validation recovery)
      const existingService = idServicoInput.value;
      const existingBarber = idBarbeiroInput.value;
      const existingDate = idDataInput.value;
      const existingHorario = idHorarioInput.value;

      // Select service
      const targetServiceId = existingService || paramService;
      if (targetServiceId) {
        const serviceCard = document.querySelector(`.service-select-item[data-service-id="${targetServiceId}"]`);
        if (serviceCard) {
          const name = serviceCard.getAttribute('data-service-name');
          const price = serviceCard.getAttribute('data-service-price');
          const duration = serviceCard.getAttribute('data-service-duration');
          selectService(targetServiceId, name, price, duration);
        }
      }

      // Select barber
      const targetBarberId = existingBarber || paramBarber;
      if (targetBarberId) {
        const barberCard = document.querySelector(`.barber-select-item[data-barber-id="${targetBarberId}"]`);
        if (barberCard) {
          const name = barberCard.getAttribute('data-barber-name');
          selectBarber(targetBarberId, name);
        }
      }

      // Select date
      if (existingDate) {
        bookingState.date = existingDate;
        const stepCard = idDataInput.closest('.step-card');
        if (stepCard) stepCard.classList.add('active');
        loadAvailableTimes();
      }

      // Select time (it will highlight once AJAX completes)
      if (existingHorario) {
        bookingState.time = existingHorario;
      }

      // Fill client details in state
      updateCustomerFields();
    };

    // Launch prepopulate check
    initPreselections();
  }

  // 3. Phone Input Mask (XX) XXXXX-XXXX
  const applyPhoneMask = (input) => {
    if (!input) return;
    
    const formatPhone = (val) => {
      let value = val.replace(/\D/g, '');
      if (value.length > 11) value = value.slice(0, 11);
      if (value.length > 10) {
        return `(${value.slice(0, 2)}) ${value.slice(2, 7)}-${value.slice(7)}`;
      } else if (value.length > 6) {
        return `(${value.slice(0, 2)}) ${value.slice(2, 6)}-${value.slice(6)}`;
      } else if (value.length > 2) {
        return `(${value.slice(0, 2)}) ${value.slice(2)}`;
      } else if (value.length > 0) {
        return `(${value}`;
      }
      return '';
    };

    // Format initial value if any
    if (input.value) {
      input.value = formatPhone(input.value);
    }

    input.addEventListener('input', (e) => {
      e.target.value = formatPhone(e.target.value);
    });
  };

  document.querySelectorAll('input[type="tel"], input[name="telefone"], #id_telefone').forEach(applyPhoneMask);
});
