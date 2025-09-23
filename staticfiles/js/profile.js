// Profile JavaScript - Interactividad para el perfil del usuario
document.addEventListener('DOMContentLoaded', function() {
    initializeProfile();
});

function initializeProfile() {
    initializeSidebarNavigation();
    initializeEditMode();
    initializeReservationFilters();
    initializePreferences();
    initializeAvatarPreview();
    initializeAnimations();
}

// Navegación del sidebar
function initializeSidebarNavigation() {
    const sidebarItems = document.querySelectorAll('.sidebar-item');
    const sections = document.querySelectorAll('.profile-section');

    sidebarItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetSection = this.getAttribute('data-section');
            
            // Remover clase activa de todos los items y secciones
            sidebarItems.forEach(si => si.classList.remove('active'));
            sections.forEach(section => section.classList.remove('active'));
            
            // Añadir clase activa al item clickeado y su sección correspondiente
            this.classList.add('active');
            const targetElement = document.getElementById(targetSection);
            if (targetElement) {
                targetElement.classList.add('active');
                
                // Scroll suave a la sección
                targetElement.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'start' 
                });
            }
        });
    });
}

// Modo de edición para información personal
function initializeEditMode() {
    window.toggleEditMode = function() {
        const form = document.getElementById('profile-form');
        const inputs = form.querySelectorAll('input[readonly], textarea[readonly]');
        const formActions = document.getElementById('form-actions');
        const editButton = document.querySelector('.btn[onclick="toggleEditMode()"]');
        
        const isReadonly = inputs[0].hasAttribute('readonly');
        
        inputs.forEach(input => {
            if (isReadonly) {
                input.removeAttribute('readonly');
                input.classList.add('editable');
            } else {
                input.setAttribute('readonly', true);
                input.classList.remove('editable');
            }
        });
        
        if (isReadonly) {
            formActions.style.display = 'block';
            editButton.innerHTML = '<i class="fas fa-times"></i> Cancelar';
            editButton.classList.remove('btn-outline-primary');
            editButton.classList.add('btn-outline-secondary');
        } else {
            formActions.style.display = 'none';
            editButton.innerHTML = '<i class="fas fa-edit"></i> Editar';
            editButton.classList.remove('btn-outline-secondary');
            editButton.classList.add('btn-outline-primary');
        }
    };
}

// Filtros de reservas mejorados
function initializeReservationFilters() {
    const statusFilter = document.getElementById('reservation-filter');
    const dateFilter = document.getElementById('date-filter');
    const sortFilter = document.getElementById('sort-filter');
    const searchInput = document.getElementById('reservation-search');
    const clearButton = document.getElementById('clear-filters');
    
    // Aplicar todos los filtros
    function applyFilters() {
        const statusValue = statusFilter ? statusFilter.value : 'all';
        const dateValue = dateFilter ? dateFilter.value : 'all';
        const sortValue = sortFilter ? sortFilter.value : 'date-desc';
        const searchValue = searchInput ? searchInput.value.toLowerCase() : '';
        
        let reservationCards = Array.from(document.querySelectorAll('.reservation-card'));
        
        // Filtrar por estado
        reservationCards.forEach(card => {
            const status = card.getAttribute('data-status');
            const statusMatch = statusValue === 'all' || status === statusValue;
            
            // Filtrar por fecha
            let dateMatch = true;
            if (dateValue !== 'all') {
                const dateElements = card.querySelectorAll('.info-item span');
                const today = new Date();
                const currentMonth = today.getMonth();
                const currentYear = today.getFullYear();
                
                // Buscar fechas en el contenido de la tarjeta
                let cardDates = [];
                dateElements.forEach(span => {
                    const text = span.textContent;
                    const dateMatch = text.match(/(\d{1,2})\/(\d{1,2})\/(\d{4})/);
                    if (dateMatch) {
                        const [, day, month, year] = dateMatch;
                        cardDates.push(new Date(year, month - 1, day));
                    }
                });
                
                if (cardDates.length > 0) {
                    const checkInDate = cardDates[0];
                    
                    switch (dateValue) {
                        case 'upcoming':
                            dateMatch = checkInDate >= today;
                            break;
                        case 'current':
                            dateMatch = checkInDate.getMonth() === currentMonth && 
                                       checkInDate.getFullYear() === currentYear;
                            break;
                        case 'past':
                            dateMatch = checkInDate < today;
                            break;
                        case 'this-year':
                            dateMatch = checkInDate.getFullYear() === currentYear;
                            break;
                    }
                }
            }
            
            // Filtrar por búsqueda
            let searchMatch = true;
            if (searchValue) {
                const cardText = card.textContent.toLowerCase();
                searchMatch = cardText.includes(searchValue);
            }
            
            // Mostrar/ocultar tarjeta
            if (statusMatch && dateMatch && searchMatch) {
                card.style.display = 'block';
                card.style.animation = 'fadeInUp 0.3s ease';
            } else {
                card.style.display = 'none';
            }
        });
        
        // Ordenar tarjetas visibles
        const visibleCards = reservationCards.filter(card => card.style.display !== 'none');
        sortReservations(visibleCards, sortValue);
    }
    
    // Función para ordenar reservas
    function sortReservations(cards, sortValue) {
        const container = document.querySelector('.reservations-container');
        if (!container) return;
        
        cards.sort((a, b) => {
            switch (sortValue) {
                case 'date-desc':
                case 'date-asc':
                    const dateA = extractDate(a);
                    const dateB = extractDate(b);
                    return sortValue === 'date-desc' ? dateB - dateA : dateA - dateB;
                    
                case 'amount-desc':
                case 'amount-asc':
                    const amountA = extractAmount(a);
                    const amountB = extractAmount(b);
                    return sortValue === 'amount-desc' ? amountB - amountA : amountA - amountB;
                    
                case 'status':
                    const statusA = a.getAttribute('data-status');
                    const statusB = b.getAttribute('data-status');
                    return statusA.localeCompare(statusB);
                    
                default:
                    return 0;
            }
        });
        
        // Reordenar en el DOM
        cards.forEach(card => container.appendChild(card));
    }
    
    // Extraer fecha de una tarjeta
    function extractDate(card) {
        const dateElement = card.querySelector('.info-item span');
        if (dateElement) {
            const dateMatch = dateElement.textContent.match(/(\d{1,2})\/(\d{1,2})\/(\d{4})/);
            if (dateMatch) {
                const [, day, month, year] = dateMatch;
                return new Date(year, month - 1, day);
            }
        }
        return new Date(0);
    }
    
    // Extraer monto de una tarjeta
    function extractAmount(card) {
        const amountElement = card.querySelector('.info-item span');
        if (amountElement) {
            const amountMatch = amountElement.textContent.match(/\$([0-9,]+)/);
            if (amountMatch) {
                return parseFloat(amountMatch[1].replace(',', ''));
            }
        }
        return 0;
    }
    
    // Event listeners
    if (statusFilter) {
        statusFilter.addEventListener('change', applyFilters);
    }
    
    if (dateFilter) {
        dateFilter.addEventListener('change', applyFilters);
    }
    
    if (sortFilter) {
        sortFilter.addEventListener('change', applyFilters);
    }
    
    if (searchInput) {
        searchInput.addEventListener('input', debounce(applyFilters, 300));
    }
    
    if (clearButton) {
        clearButton.addEventListener('click', function() {
            if (statusFilter) statusFilter.value = 'all';
            if (dateFilter) dateFilter.value = 'all';
            if (sortFilter) sortFilter.value = 'date-desc';
            if (searchInput) searchInput.value = '';
            applyFilters();
        });
    }
}

// Función debounce para optimizar la búsqueda
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Función para cancelar reservas
function cancelReservation(reservationId) {
    if (confirm('¿Estás seguro de que deseas cancelar esta reserva? Esta acción no se puede deshacer.')) {
        // Aquí se haría la petición AJAX real al servidor
        fetch(`/reservas/cancelar/${reservationId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Actualizar la tarjeta de reserva
                const reservationCard = document.querySelector(`[data-reservation-id="${reservationId}"]`);
                if (reservationCard) {
                    const statusBadge = reservationCard.querySelector('.reservation-status-badge');
                    if (statusBadge) {
                        statusBadge.textContent = 'Cancelada';
                        statusBadge.className = 'reservation-status-badge status-cancelada';
                    }
                    
                    // Actualizar el atributo data-status
                    reservationCard.setAttribute('data-status', 'cancelada');
                    
                    // Ocultar botones de acción
                    const actionButtons = reservationCard.querySelectorAll('.btn-outline-danger, .btn-outline-success');
                    actionButtons.forEach(btn => btn.style.display = 'none');
                }
                
                showNotification('Reserva cancelada exitosamente', 'success');
            } else {
                showNotification('Error al cancelar la reserva: ' + data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error al cancelar la reserva', 'error');
        });
    }
}

// Función para obtener el token CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Función para mostrar estadísticas de reservas filtradas
function updateReservationStats() {
    const visibleCards = document.querySelectorAll('.reservation-card[style*="block"], .reservation-card:not([style*="none"])');
    const totalVisible = visibleCards.length;
    
    // Contar por estado
    const stats = {
        confirmada: 0,
        pendiente: 0,
        cancelada: 0,
        activa: 0
    };
    
    visibleCards.forEach(card => {
        const status = card.getAttribute('data-status');
        if (stats.hasOwnProperty(status)) {
            stats[status]++;
        }
    });
    
    // Mostrar estadísticas en la interfaz (si existe un elemento para ello)
    const statsContainer = document.getElementById('reservation-stats');
    if (statsContainer) {
        statsContainer.innerHTML = `
            <div class="stats-summary">
                <span class="stat-item">Total: ${totalVisible}</span>
                <span class="stat-item">Confirmadas: ${stats.confirmada}</span>
                <span class="stat-item">Pendientes: ${stats.pendiente}</span>
                <span class="stat-item">Activas: ${stats.activa}</span>
                <span class="stat-item">Canceladas: ${stats.cancelada}</span>
            </div>
        `;
    }
}

// Gestión de preferencias
function initializePreferences() {
    window.savePreferences = function() {
        const preferences = {};
        const checkboxes = document.querySelectorAll('input[name^="pref_"]');
        const specialRequests = document.getElementById('special_requests');
        
        checkboxes.forEach(checkbox => {
            preferences[checkbox.name] = checkbox.checked;
        });
        
        if (specialRequests) {
            preferences.special_requests = specialRequests.value;
        }
        
        // Simular guardado (aquí se haría una petición AJAX real)
        showNotification('Preferencias guardadas exitosamente', 'success');
        
        // En una implementación real, harías algo como:
        // fetch('/api/save-preferences/', {
        //     method: 'POST',
        //     headers: {
        //         'Content-Type': 'application/json',
        //         'X-CSRFToken': getCookie('csrftoken')
        //     },
        //     body: JSON.stringify(preferences)
        // });
    };
}

// Preview del avatar
function initializeAvatarPreview() {
    window.previewAvatar = function(input) {
        if (input.files && input.files[0]) {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                const avatarImg = document.querySelector('.profile-avatar-large img');
                const avatarPlaceholder = document.querySelector('.avatar-placeholder-large');
                
                if (avatarImg) {
                    avatarImg.src = e.target.result;
                } else if (avatarPlaceholder) {
                    // Crear nueva imagen si no existe
                    const newImg = document.createElement('img');
                    newImg.src = e.target.result;
                    newImg.alt = 'Foto de perfil';
                    avatarPlaceholder.parentNode.replaceChild(newImg, avatarPlaceholder);
                }
            };
            
            reader.readAsDataURL(input.files[0]);
        }
    };
}

// Animaciones y efectos
function initializeAnimations() {
    // Animación de entrada para las tarjetas
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animation = 'fadeInUp 0.6s ease forwards';
            }
        });
    }, { threshold: 0.1 });
    
    document.querySelectorAll('.section-card, .reservation-card, .setting-card').forEach(card => {
        observer.observe(card);
    });
    
    // Efecto hover para las tarjetas de configuración
    document.querySelectorAll('.setting-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.boxShadow = '0 8px 25px rgba(0,0,0,0.1)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 4px 15px rgba(0,0,0,0.05)';
        });
    });
}

// Funciones de configuración
window.toggleNotifications = function() {
    showNotification('Configuración de notificaciones próximamente', 'info');
};

window.toggleTheme = function() {
    const body = document.body;
    const isDark = body.classList.contains('dark-theme');
    
    if (isDark) {
        body.classList.remove('dark-theme');
        localStorage.setItem('theme', 'light');
        showNotification('Tema claro activado', 'success');
    } else {
        body.classList.add('dark-theme');
        localStorage.setItem('theme', 'dark');
        showNotification('Tema oscuro activado', 'success');
    }
};

// Cancelar reserva
window.cancelReservation = function(reservationId) {
    if (confirm('¿Estás seguro de que quieres cancelar esta reserva?')) {
        // Simular cancelación (aquí se haría una petición AJAX real)
        showNotification('Reserva cancelada exitosamente', 'success');
        
        // En una implementación real:
        // fetch(`/api/reservations/${reservationId}/cancel/`, {
        //     method: 'POST',
        //     headers: {
        //         'X-CSRFToken': getCookie('csrftoken')
        //     }
        // }).then(response => {
        //     if (response.ok) {
        //         location.reload();
        //     }
        // });
    }
};

// ===== PREFERENCIAS =====
function resetPreferences() {
    if (confirm('¿Estás seguro de que quieres restablecer todas las preferencias?')) {
        const form = document.querySelector('.preferences-form');
        
        // Desmarcar todos los checkboxes
        form.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
            checkbox.checked = false;
        });
        
        // Resetear todos los selects
        form.querySelectorAll('select').forEach(select => {
            select.selectedIndex = 0;
        });
        
        showNotification('Preferencias restablecidas. No olvides guardar los cambios.', 'info');
    }
}

// Sistema de notificaciones
function showNotification(message, type = 'info') {
    // Crear elemento de notificación
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${getNotificationIcon(type)}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Añadir estilos
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${getNotificationColor(type)};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: space-between;
        min-width: 300px;
        animation: slideInRight 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remover después de 5 segundos
    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}

function getNotificationIcon(type) {
    const icons = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    return icons[type] || 'info-circle';
}

function getNotificationColor(type) {
    const colors = {
        success: '#28a745',
        error: '#dc3545',
        warning: '#ffc107',
        info: '#17a2b8'
    };
    return colors[type] || '#17a2b8';
}

// Utilidad para obtener CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Aplicar tema guardado al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
    }
});

// Añadir animaciones CSS dinámicamente
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(100%);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes slideOutRight {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }
    
    .notification-content {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .notification-close {
        background: none;
        border: none;
        color: white;
        cursor: pointer;
        padding: 5px;
        margin-left: 15px;
    }
    
    .notification-close:hover {
        opacity: 0.7;
    }
    
    .form-control.editable {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 0.2rem rgba(212, 175, 55, 0.25);
    }
    
    .dark-theme {
        --bg-color: #1a1a1a;
        --text-color: #ffffff;
        --card-bg: #2d2d2d;
        --border-color: #404040;
    }
    
    .dark-theme .section-card,
    .dark-theme .profile-sidebar,
    .dark-theme .reservation-card,
    .dark-theme .setting-card {
        background: var(--card-bg);
        border-color: var(--border-color);
        color: var(--text-color);
    }
    
    .dark-theme .profile-hero {
        background: linear-gradient(135deg, #2d2d2d, #1a1a1a);
    }
`;
document.head.appendChild(style);