function showSection(id) {
  const sections = document.querySelectorAll('.section');
  sections.forEach(section => {
    section.classList.remove('active');
  });

  const target = document.getElementById(id);
  if (target) {
    target.classList.add('active');
  }
}

function agregarCliente(event) {
  event.preventDefault();

  const nombre = document.getElementById('cliente-nombre').value;
  const email = document.getElementById('cliente-email').value;
  const telefono = document.getElementById('cliente-telefono').value;
  const documento = document.getElementById('cliente-documento').value;

  const tabla = document.getElementById('tabla-clientes');
  const fila = tabla.insertRow();

  fila.innerHTML = `
    <td>${nombre}</td>
    <td>${email}</td>
    <td>${telefono}</td>
    <td>${documento}</td>
  `;

  // Limpiar formulario
  event.target.reset();
}

function agregarHabitacion(event) {
  event.preventDefault();

  const numero = document.getElementById('habitacion-numero').value;
  const tipo = document.getElementById('habitacion-tipo').value;
  const precio = document.getElementById('habitacion-precio').value;
  const estado = document.getElementById('habitacion-estado').value;

  const tabla = document.getElementById('tabla-habitaciones');
  const fila = tabla.insertRow();

  fila.innerHTML = `
    <td>${numero}</td>
    <td>${tipo}</td>
    <td>$${precio}</td>
    <td>${estado}</td>
  `;

  // Limpiar formulario
  event.target.reset();
}

function cerrarSesion() {
  // Acción simulada: puedes redirigir, borrar localStorage, etc.
  alert("Sesión cerrada correctamente.");
  // Redireccionar (opcional)
  window.location.href = "login.html"; // Cambia a tu página de login si existe
}
