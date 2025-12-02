// DOM Elements
// DOM Elements
const navToggle = document.getElementById("nav-toggle")
const navMenu = document.getElementById("nav-menu")
const header = document.getElementById("header")
const scrollIndicator = document.querySelector(".scroll-indicator")
const bookingForm = document.getElementById("booking-form")
const contactForm = document.querySelector(".contact-form")
const newsletterForm = document.querySelector(".newsletter-form")
const profileTrigger = document.getElementById("profileTrigger")
const dropdownMenu = document.getElementById("dropdownMenu")

// Mobile Navigation Toggle
if (navToggle && navMenu) {
  navToggle.addEventListener("click", () => {
    navMenu.classList.toggle("active")
    navToggle.classList.toggle("active")
  })

  // Close mobile menu when clicking on a link
  document.querySelectorAll(".nav-link").forEach((link) => {
    link.addEventListener("click", () => {
      navMenu.classList.remove("active")
      navToggle.classList.remove("active")
    })
  })
}

// Header Scroll Effect
window.addEventListener("scroll", () => {
  if (window.scrollY > 100) {
    header.classList.add("scrolled")
  } else {
    header.classList.remove("scrolled")
  }
})

// Smooth Scrolling for Navigation Links
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener("click", function (e) {
    e.preventDefault()
    const target = document.querySelector(this.getAttribute("href"))
    if (target) {
      const headerHeight = header.offsetHeight
      const targetPosition = target.offsetTop - headerHeight

      window.scrollTo({
        top: targetPosition,
        behavior: "smooth",
      })
    }
  })
})

// Scroll Indicator Click
if (scrollIndicator) {
  scrollIndicator.addEventListener("click", () => {
    const bookingSection = document.getElementById("reservar")
    if (bookingSection) {
      const headerHeight = header.offsetHeight
      const targetPosition = bookingSection.offsetTop - headerHeight

      window.scrollTo({
        top: targetPosition,
        behavior: "smooth",
      })
    }
  })
}

// Booking Form Handler
if (bookingForm) {
  bookingForm.addEventListener("submit", function (e) {
    e.preventDefault()

    const formData = new FormData(this)
    const checkin = formData.get("checkin")
    const checkout = formData.get("checkout")
    const guests = formData.get("guests")

    // Validate dates
    const checkinDate = new Date(checkin)
    const checkoutDate = new Date(checkout)
    const today = new Date()
    today.setHours(0, 0, 0, 0)

    if (checkinDate < today) {
      showNotification("La fecha de entrada no puede ser anterior a hoy", "error")
      return
    }

    if (checkoutDate <= checkinDate) {
      showNotification("La fecha de salida debe ser posterior a la fecha de entrada", "error")
      return
    }

    // Simulate booking search
    showNotification("Buscando disponibilidad...", "info")

    setTimeout(() => {
      showNotification("¡Habitaciones disponibles encontradas! Redirigiendo...", "success")
      // Here you would typically redirect to a booking page
      // window.location.href = '/booking-results/';
    }, 2000)
  })
}

// Contact Form Handler
if (contactForm) {
  contactForm.addEventListener("submit", function (e) {
    e.preventDefault()

    const formData = new FormData(this)
    const firstName = formData.get("first_name")
    const lastName = formData.get("last_name")
    const email = formData.get("email")
    const phone = formData.get("phone")
    const subject = formData.get("subject")
    const message = formData.get("message")

    // Validaciones básicas
    if (!firstName || !lastName || !email || !subject || !message) {
      showNotification("Por favor, completa todos los campos requeridos", "error")
      return
    }

    // Validación de email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(email)) {
      showNotification("Por favor, ingresa un email válido", "error")
      return
    }

    // Simulate form submission
    showNotification("Enviando mensaje...", "info")

    // Submit form normally (Django will handle it)
    this.submit()
  })
}

// Newsletter form handler removed

// Notification System
function showNotification(message, type = "info") {
  // Remove existing notifications
  const existingNotifications = document.querySelectorAll(".notification")
  existingNotifications.forEach((notification) => notification.remove())

  // Create notification element
  const notification = document.createElement("div")
  notification.className = `notification notification-${type}`
  notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-message">${message}</span>
            <button class="notification-close">&times;</button>
        </div>
    `

  // Add styles
  notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        background: ${type === "success" ? "#27ae60" : type === "error" ? "#e74c3c" : "#3498db"};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 5px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.2);
        z-index: 10000;
        transform: translateX(400px);
        transition: transform 0.3s ease;
        max-width: 350px;
    `

  // Add to DOM
  document.body.appendChild(notification)

  // Animate in
  setTimeout(() => {
    notification.style.transform = "translateX(0)"
  }, 100)

  // Close button functionality
  const closeBtn = notification.querySelector(".notification-close")
  closeBtn.addEventListener("click", () => {
    notification.style.transform = "translateX(400px)"
    setTimeout(() => notification.remove(), 300)
  })

  // Auto remove after 5 seconds
  setTimeout(() => {
    if (notification.parentNode) {
      notification.style.transform = "translateX(400px)"
      setTimeout(() => notification.remove(), 300)
    }
  }, 5000)
}

// Set minimum date for booking form
document.addEventListener("DOMContentLoaded", () => {
  const checkinInput = document.getElementById("checkin")
  const checkoutInput = document.getElementById("checkout")

  if (checkinInput && checkoutInput) {
    const today = new Date().toISOString().split("T")[0]
    checkinInput.setAttribute("min", today)

    checkinInput.addEventListener("change", function () {
      const checkinDate = new Date(this.value)
      checkinDate.setDate(checkinDate.getDate() + 1)
      const minCheckout = checkinDate.toISOString().split("T")[0]
      checkoutInput.setAttribute("min", minCheckout)
    })
  }
})

// Intersection Observer for Animations
const observerOptions = {
  threshold: 0.1,
  rootMargin: "0px 0px -50px 0px",
}

const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.style.opacity = "1"
      entry.target.style.transform = "translateY(0)"
    }
  })
}, observerOptions)

// Observe elements for animation
document.addEventListener("DOMContentLoaded", () => {
  const animateElements = document.querySelectorAll(
    ".room-card, .service-card, .about-text, .about-image, .value-item, .team-member, .contact-item",
  )

  animateElements.forEach((el) => {
    el.style.opacity = "0"
    el.style.transform = "translateY(30px)"
    el.style.transition = "opacity 0.6s ease, transform 0.6s ease"
    observer.observe(el)
  })
})

// Lazy Loading for Images
if ("IntersectionObserver" in window) {
  const imageObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const img = entry.target
        img.src = img.dataset.src || img.src
        img.classList.remove("lazy")
        imageObserver.unobserve(img)
      }
    })
  })

  document.querySelectorAll("img[data-src]").forEach((img) => {
    imageObserver.observe(img)
  })
}

// Parallax Effect for Hero Section
window.addEventListener("scroll", () => {
  const scrolled = window.pageYOffset
  const heroImage = document.querySelector(".hero-image")

  if (heroImage && scrolled < window.innerHeight) {
    heroImage.style.transform = `translateY(${scrolled * 0.5}px)`
  }
})

// Room Card Hover Effects
document.querySelectorAll(".room-card").forEach((card) => {
  card.addEventListener("mouseenter", function () {
    this.style.transform = "translateY(-10px) scale(1.02)"
  })

  card.addEventListener("mouseleave", function () {
    this.style.transform = "translateY(0) scale(1)"
  })
})

// Service Card Animation
document.querySelectorAll(".service-card").forEach((card) => {
  card.addEventListener("mouseenter", function () {
    const icon = this.querySelector(".service-icon")
    if (icon) {
      icon.style.transform = "scale(1.2) rotate(5deg)"
    }
  })

  card.addEventListener("mouseleave", function () {
    const icon = this.querySelector(".service-icon")
    if (icon) {
      icon.style.transform = "scale(1) rotate(0deg)"
    }
  })
})

// Value Item Hover Effects
document.querySelectorAll(".value-item").forEach((item) => {
  item.addEventListener("mouseenter", function () {
    const icon = this.querySelector(".value-icon")
    if (icon) {
      icon.style.transform = "scale(1.2) rotate(10deg)"
    }
  })

  item.addEventListener("mouseleave", function () {
    const icon = this.querySelector(".value-icon")
    if (icon) {
      icon.style.transform = "scale(1) rotate(0deg)"
    }
  })
})

// Team Member Hover Effects
document.querySelectorAll(".team-member").forEach((member) => {
  member.addEventListener("mouseenter", function () {
    const photo = this.querySelector(".member-photo")
    if (photo) {
      photo.style.transform = "scale(1.05)"
    }
  })

  member.addEventListener("mouseleave", function () {
    const photo = this.querySelector(".member-photo")
    if (photo) {
      photo.style.transform = "scale(1)"
    }
  })
})

// Contact Item Hover Effects
document.querySelectorAll(".contact-item").forEach((item) => {
  item.addEventListener("mouseenter", function () {
    const icon = this.querySelector(".contact-icon")
    if (icon) {
      icon.style.transform = "scale(1.2) rotate(-5deg)"
    }
  })

  item.addEventListener("mouseleave", function () {
    const icon = this.querySelector(".contact-icon")
    if (icon) {
      icon.style.transform = "scale(1) rotate(0deg)"
    }
  })
})

// Room Filters Functionality
let applyFilters // Declare applyFilters variable here

document.addEventListener("DOMContentLoaded", () => {
  const filterForm = document.getElementById("filter-form")
  const clearFiltersBtn = document.getElementById("clear-filters")
  const roomsGrid = document.getElementById("rooms-grid")

  if (filterForm && roomsGrid) {
    // Filter form handler
    filterForm.addEventListener("submit", (e) => {
      e.preventDefault()
      applyFilters()
    })

    // Clear filters handler
    if (clearFiltersBtn) {
      clearFiltersBtn.addEventListener("click", () => {
        filterForm.reset()
        applyFilters()
        showNotification("Filtros limpiados", "info")
      })
    }

    // Real-time filtering on input change
    const filterInputs = filterForm.querySelectorAll("input, select")
    filterInputs.forEach((input) => {
      input.addEventListener("change", applyFilters)
    })

    applyFilters = () => {
      const formData = new FormData(filterForm)
      const filters = {
        tipo: formData.get("tipo") || "",
        precioMin: Number.parseInt(formData.get("precio-min")) || 0,
        precioMax: Number.parseInt(formData.get("precio-max")) || 9999,
        capacidad: formData.get("capacidad") || "",
      }

      const roomCards = roomsGrid.querySelectorAll(".room-card")
      let visibleCount = 0

      roomCards.forEach((card) => {
        const cardTipo = card.dataset.tipo || ""
        const cardPrecio = Number.parseInt(card.dataset.precio) || 0
        const cardCapacidad = card.dataset.capacidad || ""

        let shouldShow = true

        // Filter by type
        if (filters.tipo && !cardTipo.includes(filters.tipo)) {
          shouldShow = false
        }

        // Filter by price range
        if (cardPrecio < filters.precioMin || cardPrecio > filters.precioMax) {
          shouldShow = false
        }

        // Filter by capacity
        if (filters.capacidad) {
          const requiredCapacity = Number.parseInt(filters.capacidad)
          const roomCapacity = Number.parseInt(cardCapacidad)
          if (roomCapacity < requiredCapacity) {
            shouldShow = false
          }
        }

        // Show/hide card with animation
        if (shouldShow) {
          card.style.display = "block"
          card.style.opacity = "0"
          card.style.transform = "translateY(20px)"
          setTimeout(
            () => {
              card.style.opacity = "1"
              card.style.transform = "translateY(0)"
            },
            100 + visibleCount * 50,
          )
          visibleCount++
        } else {
          card.style.opacity = "0"
          card.style.transform = "translateY(-20px)"
          setTimeout(() => {
            card.style.display = "none"
          }, 300)
        }
      })

      // Show no results message if no rooms visible
      let noResultsMsg = roomsGrid.querySelector(".no-results")
      if (visibleCount === 0) {
        if (!noResultsMsg) {
          noResultsMsg = document.createElement("div")
          noResultsMsg.className = "no-results"
          noResultsMsg.innerHTML = `
                        <div style="grid-column: 1 / -1; text-align: center; padding: 4rem 2rem; color: var(--text-light);">
                            <i class="fas fa-search" style="font-size: 4rem; color: var(--primary-color); margin-bottom: 1rem;"></i>
                            <h3 style="color: var(--secondary-color); margin-bottom: 0.5rem;">No se encontraron habitaciones</h3>
                            <p>Intenta ajustar los filtros para encontrar habitaciones disponibles.</p>
                        </div>
                    `
          roomsGrid.appendChild(noResultsMsg)
        }
        noResultsMsg.style.display = "block"
      } else {
        if (noResultsMsg) {
          noResultsMsg.style.display = "none"
        }
      }

      // Update results count
      updateResultsCount(visibleCount)
    }

    function updateResultsCount(count) {
      let countElement = document.querySelector(".results-count")
      if (!countElement) {
        countElement = document.createElement("div")
        countElement.className = "results-count"
        countElement.style.cssText = `
                    text-align: center;
                    margin: 1rem 0;
                    color: var(--text-light);
                    font-weight: 600;
                `
        const container = roomsGrid.parentElement
        container.insertBefore(countElement, roomsGrid)
      }

      countElement.textContent = `${count} habitación${count !== 1 ? "es" : ""} encontrada${count !== 1 ? "s" : ""}`
    }

    // Initialize filters
    applyFilters()
  }

  // Room card enhanced interactions
  const roomCards = document.querySelectorAll(".room-card")
  roomCards.forEach((card) => {
    // Enhanced hover effects
    card.addEventListener("mouseenter", function () {
      this.style.transform = "translateY(-8px)"
      this.style.boxShadow = "var(--shadow-heavy)"

      // Animate price badge
      const priceElement = this.querySelector(".room-price")
      if (priceElement) {
        priceElement.style.transform = "scale(1.05)"
      }

      // Animate amenities
      const amenities = this.querySelectorAll(".amenity")
      amenities.forEach((amenity, index) => {
        setTimeout(() => {
          amenity.style.transform = "translateY(-2px)"
        }, index * 50)
      })
    })

    card.addEventListener("mouseleave", function () {
      this.style.transform = "translateY(0)"
      this.style.boxShadow = "var(--shadow-light)"

      // Reset price badge
      const priceElement = this.querySelector(".room-price")
      if (priceElement) {
        priceElement.style.transform = "scale(1)"
      }

      // Reset amenities
      const amenities = this.querySelectorAll(".amenity")
      amenities.forEach((amenity) => {
        amenity.style.transform = "translateY(0)"
      })
    })

    // Add to cart button enhancement
    const addToCartBtn = card.querySelector('a[href*="agregar_al_carrito"]')
    if (addToCartBtn) {
      addToCartBtn.addEventListener("click", function (e) {
        e.preventDefault()

        // Add loading state
        const originalText = this.innerHTML
        this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Agregando...'
        this.style.pointerEvents = "none"

        // Simulate adding to cart
        setTimeout(() => {
          this.innerHTML = '<i class="fas fa-check"></i> Agregado'
          this.style.background = "var(--accent-color)"

          showNotification("Habitación agregada al carrito", "success")

          // Reset button after 2 seconds
          setTimeout(() => {
            this.innerHTML = originalText
            this.style.background = "var(--primary-color)"
            this.style.pointerEvents = "auto"
          }, 2000)
        }, 1000)
      })
    }
  })

  // Price range slider enhancement
  const priceMinInput = document.getElementById("precio-min")
  const priceMaxInput = document.getElementById("precio-max")

  if (priceMinInput && priceMaxInput) {
    // Add real-time price validation
    priceMinInput.addEventListener("input", function () {
      const minValue = Number.parseInt(this.value) || 0
      const maxValue = Number.parseInt(priceMaxInput.value) || 9999

      if (minValue > maxValue) {
        priceMaxInput.value = minValue
      }
    })

    priceMaxInput.addEventListener("input", function () {
      const maxValue = Number.parseInt(this.value) || 9999
      const minValue = Number.parseInt(priceMinInput.value) || 0

      if (maxValue < minValue) {
        priceMinInput.value = maxValue
      }
    })
  }
})

// Quick search functionality
function addQuickSearch() {
  const roomsListing = document.querySelector(".rooms-listing")
  if (!roomsListing) return

  const searchContainer = document.createElement("div")
  searchContainer.className = "quick-search-container"
  searchContainer.style.cssText = `
        background: var(--white);
        padding: 1rem;
        border-radius: 10px;
        box-shadow: var(--shadow-light);
        margin-bottom: 2rem;
    `

  searchContainer.innerHTML = `
        <div style="display: flex; gap: 1rem; align-items: center; flex-wrap: wrap;">
            <div style="flex: 1; min-width: 250px;">
                <input type="text" id="quick-search" placeholder="Buscar habitaciones..." 
                       style="width: 100%; padding: 0.75rem; border: 2px solid #e0e0e0; border-radius: 5px; font-size: 1rem;">
            </div>
            <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                <button class="quick-filter-btn" data-filter="individual">Individual</button>
                <button class="quick-filter-btn" data-filter="doble">Doble</button>
                <button class="quick-filter-btn" data-filter="suite">Suite</button>
                <button class="quick-filter-btn" data-filter="presidencial">Presidencial</button>
            </div>
        </div>
    `

  const container = roomsListing.querySelector(".container")
  container.insertBefore(searchContainer, container.firstChild)

  // Style quick filter buttons
  const quickFilterBtns = searchContainer.querySelectorAll(".quick-filter-btn")
  quickFilterBtns.forEach((btn) => {
    btn.style.cssText = `
            padding: 0.5rem 1rem;
            border: 2px solid var(--primary-color);
            background: transparent;
            color: var(--primary-color);
            border-radius: 20px;
            cursor: pointer;
            transition: var(--transition);
            font-weight: 600;
        `

    btn.addEventListener("click", function () {
      // Toggle active state
      const isActive = this.classList.contains("active")

      // Remove active from all buttons
      quickFilterBtns.forEach((b) => {
        b.classList.remove("active")
        b.style.background = "transparent"
        b.style.color = "var(--primary-color)"
      })

      if (!isActive) {
        this.classList.add("active")
        this.style.background = "var(--primary-color)"
        this.style.color = "var(--white)"

        // Set filter
        const tipoSelect = document.getElementById("tipo")
        if (tipoSelect) {
          tipoSelect.value = this.dataset.filter
          applyFilters()
        }
      } else {
        // Clear filter
        const tipoSelect = document.getElementById("tipo")
        if (tipoSelect) {
          tipoSelect.value = ""
          applyFilters()
        }
      }
    })
  })

  // Quick search input
  const quickSearchInput = document.getElementById("quick-search")
  if (quickSearchInput) {
    quickSearchInput.addEventListener("input", function () {
      const searchTerm = this.value.toLowerCase()
      const roomCards = document.querySelectorAll(".room-card")

      roomCards.forEach((card) => {
        const roomTitle = card.querySelector("h3").textContent.toLowerCase()
        const roomDescription = card.querySelector(".room-description").textContent.toLowerCase()
        const roomType = card.querySelector(".room-type").textContent.toLowerCase()

        const matches =
          roomTitle.includes(searchTerm) || roomDescription.includes(searchTerm) || roomType.includes(searchTerm)

        if (matches || searchTerm === "") {
          card.style.display = "block"
          card.style.opacity = "1"
        } else {
          card.style.display = "none"
          card.style.opacity = "0"
        }
      })
    })
  }
}

// Initialize quick search when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  setTimeout(addQuickSearch, 100)
})

// Profile Dropdown Functionality
document.addEventListener("DOMContentLoaded", () => {
  if (profileTrigger && dropdownMenu) {
    // Toggle dropdown on click
    profileTrigger.addEventListener("click", (e) => {
      e.preventDefault()
      e.stopPropagation()
      dropdownMenu.classList.toggle("active")
    })

    // Close dropdown when clicking outside
    document.addEventListener("click", (e) => {
      if (!profileTrigger.contains(e.target) && !dropdownMenu.contains(e.target)) {
        dropdownMenu.classList.remove("active")
      }
    })

    // Close dropdown when pressing Escape
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        dropdownMenu.classList.remove("active")
      }
    })

    // Close dropdown when clicking on menu items
    const dropdownItems = dropdownMenu.querySelectorAll(".dropdown-item")
    dropdownItems.forEach((item) => {
      item.addEventListener("click", () => {
        dropdownMenu.classList.remove("active")
      })
    })

    // Add smooth animation for dropdown arrow
    const dropdownArrow = profileTrigger.querySelector(".dropdown-arrow")
    if (dropdownArrow) {
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (mutation.type === "attributes" && mutation.attributeName === "class") {
            if (dropdownMenu.classList.contains("active")) {
              dropdownArrow.style.transform = "rotate(180deg)"
            } else {
              dropdownArrow.style.transform = "rotate(0deg)"
            }
          }
        })
      })

      observer.observe(dropdownMenu, { attributes: true })
    }
  }
})

console.log("Hotel Elegante - Website loaded successfully! 🏨")

// Obtener CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Función para actualizar contador y total
function actualizarResumen() {
    const contenedor = document.getElementById("servicios-seleccionados");
    const servicios = contenedor.querySelectorAll(".servicio-agregado");
    const contador = document.getElementById("servicios-count");
    const total = document.getElementById("total-servicios");

    let totalPrecio = 0;
    servicios.forEach(s => {
        totalPrecio += parseFloat(s.dataset.precio);
    });

    contador.textContent = servicios.length;
    total.textContent = `$${totalPrecio}`;

    document.getElementById("continuar-reserva").disabled = servicios.length === 0;
}

// Manejar click en botones agregar
if (!(window && window.SERVICIOS_INLINE)) {
  document.querySelectorAll(".agregar-servicio").forEach((btn) => {
      btn.addEventListener("click", function() {
          const servicioId = this.dataset.id;

          fetch("/reservas/servicio/agregar/", {
              method: "POST",
              headers: {
                  "Content-Type": "application/json",
                  "X-CSRFToken": getCookie("csrftoken")
              },
              body: JSON.stringify({ servicio_id: servicioId })
          })
          .then(res => res.json())
          .then(data => {
              if (data.success) {
                  showNotification(`Servicio "${data.servicio.nombre}" agregado`, "success");

                  // Actualizar la lista de servicios seleccionados
                  const contenedor = document.getElementById("servicios-seleccionados");
                  const emptyState = contenedor.querySelector(".empty-state");
                  if (emptyState) emptyState.remove();

                  const servicioDiv = document.createElement("div");
                  servicioDiv.className = "d-flex justify-content-between align-items-center mb-2 servicio-agregado";
                  servicioDiv.dataset.id = data.servicio.id;
                  servicioDiv.dataset.precio = data.servicio.precio;
                  servicioDiv.innerHTML = `
                      <span>${data.servicio.nombre}</span>
                      <div>
                          <span>$${data.servicio.precio}</span>
                          <button class="btn btn-sm btn-outline-danger ms-2 eliminar-servicio">
                              <i class="fas fa-trash"></i>
                          </button>
                      </div>
                  `;
                  contenedor.appendChild(servicioDiv);

                  // Manejar eliminar servicio
                  servicioDiv.querySelector(".eliminar-servicio").addEventListener("click", function() {
                      servicioDiv.remove();
                      showNotification(`Servicio "${data.servicio.nombre}" eliminado`, "info");
                      actualizarResumen();

                      // Si no quedan servicios, mostrar estado vacío
                      if (contenedor.querySelectorAll(".servicio-agregado").length === 0) {
                          const emptyDiv = document.createElement("div");
                          emptyDiv.className = "empty-state text-center py-4";
                          emptyDiv.innerHTML = `
                              <i class="fas fa-plus-circle fa-3x text-muted mb-3"></i>
                              <p class="text-muted mb-0">Selecciona servicios para personalizar tu experiencia</p>
                          `;
                          contenedor.appendChild(emptyDiv);
                      }
                  });

                  actualizarResumen();
              }
          })
          .catch(() => {
              showNotification("No se pudo agregar el servicio", "danger");
          });
      });
  });
