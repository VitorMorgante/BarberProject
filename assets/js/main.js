/**
 * Delacruz Barber - Premium Interactive Frontend Logic
 * Implements smooth scroll, gallery filtering, booking state wizard, and storage persistence.
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

  // Mobile navbar closing on link click
  const navbarCollapse = document.querySelector('.navbar-collapse');
  const navbarToggler = document.querySelector('.navbar-toggler');
  navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      // Smooth scroll adjustment
      e.preventDefault();
      const targetId = link.getAttribute('href');
      const targetSection = document.querySelector(targetId);

      if (targetSection) {
        const offsetPosition = targetSection.offsetTop - 85; // navbar offset
        window.scrollTo({
          top: offsetPosition,
          behavior: 'smooth'
        });
      }

      // Bootstrap collapse close
      if (navbarCollapse.classList.contains('show')) {
        navbarToggler.click();
      }
    });
  });

  // Hero custom link buttons
  const heroCTAButtons = document.querySelectorAll('.hero-scroll-btn');
  heroCTAButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = btn.getAttribute('href');
      const targetSection = document.querySelector(targetId);
      if (targetSection) {
        const offsetPosition = targetSection.offsetTop - 85;
        window.scrollTo({
          top: offsetPosition,
          behavior: 'smooth'
        });
      }
    });
  });

  // 2. Booking Wizard - Service Selection
  const serviceItems = document.querySelectorAll('.service-select-item');
  const bookingServiceBtn = document.querySelectorAll('.booking-trigger-service'); // Buttons from primary services list triggering booking

  const selectService = (id, name, price, duration) => {
    bookingState.serviceId = id;
    bookingState.serviceName = name;
    bookingState.servicePrice = parseFloat(price);
    bookingState.serviceDuration = duration;

    // Update wizard highlight
    serviceItems.forEach(item => {
      if (item.getAttribute('data-service-id') === id) {
        item.classList.add('selected');
        // Visually trigger check in siblings
        const cardHeader = item.closest('.step-card');
        if (cardHeader) cardHeader.classList.add('active');
      } else {
        item.classList.remove('selected');
      }
    });

    updateSummary();
  };

  serviceItems.forEach(item => {
    item.addEventListener('click', () => {
      const id = item.getAttribute('data-service-id');
      const name = item.getAttribute('data-service-name');
      const price = item.getAttribute('data-service-price');
      const duration = item.getAttribute('data-service-duration');
      selectService(id, name, price, duration);
    });
  });

  // Link services card CTA to preselect service and scroll down
  bookingServiceBtn.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const sId = btn.getAttribute('data-s-id');
      const sName = btn.getAttribute('data-s-name');
      const sPrice = btn.getAttribute('data-s-price');
      const sDuration = btn.getAttribute('data-s-duration');

      selectService(sId, sName, sPrice, sDuration);

      // Scroll smoothly to appointment section
      const schedSec = document.querySelector('#agendamento');
      if (schedSec) {
        const offsetPosition = schedSec.offsetTop - 85;
        window.scrollTo({
          top: offsetPosition,
          behavior: 'smooth'
        });
      }
    });
  });

  // 3. Booking Wizard - Barber Selection
  const barberItems = document.querySelectorAll('.barber-select-item');
  const bookingBarberBtn = document.querySelectorAll('.booking-trigger-barber');

  const selectBarber = (id, name) => {
    bookingState.barberId = id;
    bookingState.barberName = name;

    barberItems.forEach(item => {
      if (item.getAttribute('data-barber-id') === id) {
        item.classList.add('selected');
        const cardHeader = item.closest('.step-card');
        if (cardHeader) cardHeader.classList.add('active');
      } else {
        item.classList.remove('selected');
      }
    });

    updateSummary();
  };

  barberItems.forEach(item => {
    item.addEventListener('click', () => {
      const id = item.getAttribute('data-barber-id');
      const name = item.getAttribute('data-barber-name');
      selectBarber(id, name);
    });
  });

  // Link barbers card select to preselect barber and scroll down
  bookingBarberBtn.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const bId = btn.getAttribute('data-b-id');
      const bName = btn.getAttribute('data-b-name');

      selectBarber(bId, bName);

      const schedSec = document.querySelector('#agendamento');
      if (schedSec) {
        const offsetPosition = schedSec.offsetTop - 85;
        window.scrollTo({
          top: offsetPosition,
          behavior: 'smooth'
        });
      }
    });
  });

  // 4. Booking Wizard - Date Selection
  const dateInput = document.getElementById('booking-date');
  if (dateInput) {
    // Set minimal date placeholder as today's date
    const today = new Date();
    const yyyy = today.getFullYear();
    const mm = String(today.getMonth() + 1).padStart(2, '0');
    const dd = String(today.getDate()).padStart(2, '0');
    
    // Set min date to today boundary so customer can't book in past
    dateInput.min = `${yyyy}-${mm}-${dd}`;

    dateInput.addEventListener('change', (e) => {
      bookingState.date = e.target.value;
      const cardHeader = dateInput.closest('.step-card');
      if (bookingState.date) {
        if (cardHeader) cardHeader.classList.add('active');
      } else {
        if (cardHeader) cardHeader.classList.remove('active');
      }
      updateSummary();
    });
  }

  // 5. Booking Wizard - Time Selection
  const timeButtons = document.querySelectorAll('.time-btn');
  timeButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      // Clear siblings in slot
      timeButtons.forEach(b => b.classList.remove('selected'));
      
      btn.classList.add('selected');
      bookingState.time = btn.getAttribute('data-time');
      const cardHeader = btn.closest('.step-card');
      if (cardHeader) cardHeader.classList.add('active');
      
      updateSummary();
    });
  });

  // 6. Booking Wizard - Customer Form Inputs
  const formName = document.getElementById('customer-name');
  const formPhone = document.getElementById('customer-phone');
  const formEmail = document.getElementById('customer-email');
  const formNotes = document.getElementById('customer-notes');

  const updateCustomerField = () => {
    bookingState.customer.name = formName ? formName.value.trim() : '';
    bookingState.customer.phone = formPhone ? formPhone.value.trim() : '';
    bookingState.customer.email = formEmail ? formEmail.value.trim() : '';
    bookingState.customer.notes = formNotes ? formNotes.value.trim() : '';

    const hasRequired = bookingState.customer.name && bookingState.customer.phone && bookingState.customer.email;
    const cardHeader = document.querySelector('#customer-step-card');
    if (hasRequired) {
      if (cardHeader) cardHeader.classList.add('active');
    } else {
      if (cardHeader) cardHeader.classList.remove('active');
    }

    updateSummary();
  };

  [formName, formPhone, formEmail, formNotes].forEach(field => {
    if (field) {
      field.addEventListener('input', updateCustomerField);
    }
  });

  // 7. Update visual appointment summary on changes
  const updateSummary = () => {
    // Labels in DOM
    const sumService = document.getElementById('sum-service-val');
    const sumBarber = document.getElementById('sum-barber-val');
    const sumDate = document.getElementById('sum-date-val');
    const sumTime = document.getElementById('sum-time-val');
    const sumClientName = document.getElementById('sum-client-val');
    const sumPhoneName = document.getElementById('sum-phone-val');
    const sumDuration = document.getElementById('sum-duration-val');
    const sumTotalPrice = document.getElementById('sum-total-price');

    // Values Formatting
    if (sumService) sumService.textContent = bookingState.serviceName || 'Não selecionado';
    if (sumBarber) sumBarber.textContent = bookingState.barberName || 'Não selecionado';
    if (sumDuration) sumDuration.textContent = bookingState.serviceDuration 
      ? `${bookingState.serviceDuration}` 
      : 'Não selecionado';

    if (sumDate) {
      if (bookingState.date) {
        // Convert yyyy-mm-dd to dd/mm/yyyy for Brazilian users
        const dateParts = bookingState.date.split('-');
        if (dateParts.length === 3) {
          sumDate.textContent = `${dateParts[2]}/${dateParts[1]}/${dateParts[0]}`;
        } else {
          sumDate.textContent = bookingState.date;
        }
      } else {
        sumDate.textContent = 'Não selecionado';
      }
    }

    if (sumTime) sumTime.textContent = bookingState.time ? `${bookingState.time}` : 'Não selecionado';
    if (sumClientName) sumClientName.textContent = bookingState.customer.name || 'Não informado';
    if (sumPhoneName) sumPhoneName.textContent = bookingState.customer.phone || 'Não informado';
    
    if (sumTotalPrice) {
      sumTotalPrice.textContent = bookingState.servicePrice 
        ? `R$ ${bookingState.servicePrice.toFixed(2).replace('.', ',')}`
        : 'R$ 0,00';
    }

    // Enable/disable confirmation button
    const confirmBtn = document.getElementById('btn-confirm-appointment');
    if (confirmBtn) {
      const isValid = bookingState.serviceId && 
                      bookingState.barberId && 
                      bookingState.date && 
                      bookingState.time && 
                      bookingState.customer.name && 
                      bookingState.customer.phone && 
                      validateEmailFormat(bookingState.customer.email);
      confirmBtn.disabled = !isValid;
    }
  };

  const validateEmailFormat = (email) => {
    if (!email) return false;
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  };

  // 8. Appointment validation errors display
  const btnValidatorFeedback = document.getElementById('btn-confirm-appointment');
  if (btnValidatorFeedback) {
    btnValidatorFeedback.addEventListener('click', (e) => {
      e.preventDefault();
      
      // Secondary check
      if (!bookingState.serviceId) {
        showValidationAlert('Por favor, selecione um Serviço no Passo 1.');
        return;
      }
      if (!bookingState.barberId) {
        showValidationAlert('Por favor, selecione um Barbeiro no Passo 2.');
        return;
      }
      if (!bookingState.date) {
        showValidationAlert('Por favor, escolha uma data no Passo 3.');
        return;
      }
      if (!bookingState.time) {
        showValidationAlert('Por favor, escolha um horário no Passo 4.');
        return;
      }
      if (!bookingState.customer.name) {
        showValidationAlert('Por favor, preencha seu Nome Completo.');
        return;
      }
      if (!bookingState.customer.phone) {
        showValidationAlert('Por favor, informe seu WhatsApp para confirmação.');
        return;
      }
      if (!validateEmailFormat(bookingState.customer.email)) {
        showValidationAlert('Por favor, insira um e-mail válido.');
        return;
      }

      // Success! Perform submit saving to localStorage
      saveAppointmentData(bookingState);
    });
  }

  const showValidationAlert = (message) => {
    alert(message);
  };

  // 9. Save Appointment Data to localStorage & Display Receipt Modal
  const saveAppointmentData = (state) => {
    try {
      const appointments = JSON.parse(localStorage.getItem('delacruz_appointments') || '[]');
      
      const newBooking = {
        id: 'DCB' + Math.floor(100000 + Math.random() * 900000),
        timestamp: new Date().toISOString(),
        serviceId: state.serviceId,
        serviceName: state.serviceName,
        price: state.servicePrice,
        duration: state.serviceDuration,
        barberId: state.barberId,
        barberName: state.barberName,
        date: state.date,
        time: state.time,
        client: { ...state.customer }
      };

      appointments.push(newBooking);
      localStorage.setItem('delacruz_appointments', JSON.stringify(appointments));

      // Show Bootstrap Modal Receipt
      populateReceiptModal(newBooking);
      const bookingSuccessModal = new bootstrap.Modal(document.getElementById('receiptModal'));
      bookingSuccessModal.show();

      // Reset Booking Wizard state
      resetBookingWizard();
    } catch (e) {
      console.error('Error saving appointment data:', e);
      alert('Houve um erro salvando seu agendamento, por favor tente novamente.');
    }
  };

  const populateReceiptModal = (booking) => {
    // Fill receipt fields
    document.getElementById('receipt-id').textContent = booking.id;
    document.getElementById('receipt-service').textContent = booking.serviceName;
    document.getElementById('receipt-barber').textContent = booking.barberName;
    
    const dateParts = booking.date.split('-');
    document.getElementById('receipt-date').textContent = `${dateParts[2]}/${dateParts[1]}/${dateParts[0]}`;
    document.getElementById('receipt-time').textContent = booking.time;
    document.getElementById('receipt-price').textContent = `R$ ${booking.price.toFixed(2).replace('.', ',')}`;
    
    document.getElementById('receipt-client').textContent = booking.client.name;
    document.getElementById('receipt-phone').textContent = booking.client.phone;
  };

  const resetBookingWizard = () => {
    // Nullify properties
    bookingState.serviceId = '';
    bookingState.serviceName = '';
    bookingState.servicePrice = 0;
    bookingState.serviceDuration = '';
    bookingState.barberId = '';
    bookingState.barberName = '';
    bookingState.date = '';
    bookingState.time = '';
    bookingState.customer.name = '';
    bookingState.customer.phone = '';
    bookingState.customer.email = '';
    bookingState.customer.notes = '';

    // Clear selections in DOM
    serviceItems.forEach(i => i.classList.remove('selected'));
    barberItems.forEach(i => i.classList.remove('selected'));
    timeButtons.forEach(i => i.classList.remove('selected'));
    
    if (dateInput) dateInput.value = '';
    if (formName) formName.value = '';
    if (formPhone) formPhone.value = '';
    if (formEmail) formEmail.value = '';
    if (formNotes) formNotes.value = '';

    // Deactivate highlight classes on step cards
    document.querySelectorAll('.step-card').forEach(card => {
      card.classList.remove('active');
    });

    updateSummary();
  };

  // 10. Gallery Category Dynamic Filters
  const filterButtons = document.querySelectorAll('.gallery-filter-btn');
  const galleryCols = document.querySelectorAll('.gallery-col');

  filterButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      // Remove active states from all sibling filter buttons
      filterButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const filterValue = btn.getAttribute('data-filter');

      galleryCols.forEach(col => {
        if (filterValue === 'all' || col.getAttribute('data-category') === filterValue) {
          col.classList.remove('hide');
          col.style.display = 'block'; // Make sure bootstrap grid works
        } else {
          col.classList.add('hide');
          col.style.display = 'none';
        }
      });
    });
  });

  // 11. Contact Form Client-Side Validation & Feedback Toast
  const contactForm = document.getElementById('contact-form');
  const contactAlertContainer = document.getElementById('contact-alert-container');

  if (contactForm && contactAlertContainer) {
    contactForm.addEventListener('submit', (e) => {
      e.preventDefault();

      const nameField = document.getElementById('contact-name');
      const emailField = document.getElementById('contact-email');
      const phoneField = document.getElementById('contact-phone');
      const messageField = document.getElementById('contact-message');

      const name = nameField ? nameField.value.trim() : '';
      const email = emailField ? emailField.value.trim() : '';
      const phone = phoneField ? phoneField.value.trim() : '';
      const msg = messageField ? messageField.value.trim() : '';

      if (!name || !email || !phone || !msg) {
        alert('Por favor, preencha todos os campos do formulário para nos enviar uma mensagem.');
        return;
      }

      if (!validateEmailFormat(email)) {
        alert('Por favor, forneça um endereço de e-mail válido.');
        return;
      }

      // Show premium success banner in container
      contactAlertContainer.innerHTML = `
        <div class="alert alert-gold-success alert-dismissible fade show border-0" role="alert" id="contactSuccessAlert">
          <i class="bi bi-patch-check-fill text-success me-2"></i>
          <strong>Mensagem enviada com sucesso!</strong> A equipe da Delacruz Barber agradece o contato e responderá no e-mail informado o quanto antes.
          <button type="button" class="btn-close btn-close-white" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
      `;

      // Reset contact fields
      contactForm.reset();

      // Scroll slightly down to alert focus
      contactAlertContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    });
  }
});
