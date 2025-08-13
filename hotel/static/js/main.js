// DOM Elements
const navToggle = document.getElementById("nav-toggle")
const navMenu = document.getElementById("nav-menu")
const header = document.getElementById("header")
const scrollIndicator = document.querySelector(".scroll-indicator")
const bookingForm = document.getElementById("booking-form")
const contactForm = document.querySelector(".contact-form")
// const newsletterForm = document.querySelector(".newsletter-form")

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

console.log("Hotel Elegante - Website loaded successfully! 🏨")
