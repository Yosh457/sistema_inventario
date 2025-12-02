document.addEventListener('DOMContentLoaded', function() {
    
    // --- LÓGICA DE FILTROS DINÁMICOS ---
    const catSelect = document.getElementById('filtro_categoria');
    const subSelect = document.getElementById('filtro_subcategoria');
    
    // Solo ejecutamos si existen los elementos (para evitar errores en otras páginas)
    if (catSelect && subSelect) {
        // Recuperar valor previo si existe (inyectado como atributo data en el HTML)
        const subActual = subSelect.getAttribute('data-selected') || "";

        function cargarSubs(catId, seleccionada = null) {
            subSelect.innerHTML = '<option value="">Todas</option>';
            subSelect.disabled = true;

            if (!catId) return;

            fetch(`/inventario/api/subcategorias/${catId}`)
                .then(res => res.json())
                .then(data => {
                    data.forEach(sub => {
                        const opt = document.createElement('option');
                        opt.value = sub.id;
                        opt.textContent = sub.nombre;
                        if (sub.id == seleccionada) opt.selected = true;
                        subSelect.appendChild(opt);
                    });
                    subSelect.disabled = false;
                })
                .catch(err => console.error("Error cargando subs:", err));
        }

        // Carga inicial
        if (catSelect.value) {
            cargarSubs(catSelect.value, subActual);
        }

        // Evento cambio
        catSelect.addEventListener('change', function() {
            cargarSubs(this.value);
        });
    }

    // --- LÓGICA DE MODAL ELIMINAR ---
    const modalEliminar = document.getElementById('modal-eliminar');
    const btnConfirmar = document.getElementById('btn-confirmar-eliminar');
    const btnCancelar = document.querySelector('#modal-eliminar .btn-secondary'); // Botón Cancelar del modal
    let idEliminarActual = null;

    // Función global para abrir el modal (necesitamos que sea global para el onclick del HTML)
    window.abrirModalEliminar = function(id, nombre) {
        if (modalEliminar) {
            document.getElementById('nombre-item-eliminar').textContent = nombre;
            modalEliminar.classList.remove('hidden');
            idEliminarActual = id;
        }
    };

    // Cerrar modal
    if (btnCancelar) {
        btnCancelar.addEventListener('click', function() {
            modalEliminar.classList.add('hidden');
        });
    }

    // Confirmar eliminación
    if (btnConfirmar) {
        btnConfirmar.addEventListener('click', function() {
            if (idEliminarActual) {
                const form = document.getElementById('form-eliminar-' + idEliminarActual);
                if (form) form.submit();
            }
        });
    }
});