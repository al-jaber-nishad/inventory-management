// Sale Form JavaScript
(function() {
    'use strict';

    function initSelect2() {
        $('.select2_search').select2({
            width: '100%',
            placeholder: 'Select an option'
        });
    }

    $(document).ready(function() {
        initSelect2();

        // Focus search box when Select2 dropdown opens
        $(document).on('select2:open', () => {
            setTimeout(() => {
                document.querySelector('.select2-container--open .select2-search__field')?.focus();
            }, 0);
        });

        // Set current date on form load if field is empty
        const saleDateInput = $('input[name="sale_date"]');
        if (!saleDateInput.val()) {
            const today = new Date();
            const formattedDate = String(today.getDate()).padStart(2, '0') + '-' +
                                String(today.getMonth() + 1).padStart(2, '0') + '-' +
                                today.getFullYear();
            saleDateInput.val(formattedDate);
        }

        let formCount = parseInt($('#id_items-TOTAL_FORMS').val());

        // Add new item row
        $(document).on('click', '.add-item', function() {
            const template = $('#empty-item-row').html();
            const newRow = template.replace(/__prefix__/g, formCount);
            $('#items-table-body').append(newRow);
            formCount++;
            $('#id_items-TOTAL_FORMS').val(formCount);

            initSelect2();
            updateCalculations();
        });

        // Remove item row
        $(document).on('click', '.remove-item', function() {
            $(this).closest('tr').remove();
            updateCalculations();
            if (typeof window.refreshProductListing === 'function') {
                window.refreshProductListing();
            }
        });

        // Handle product selection to populate price
        $(document).on('change', 'select[name*="product"]', function() {
            const productId = $(this).val();
            const row = $(this).closest('tr');
            const priceInput = row.find('.price-input');

            if (productId) {
                $.get(`/sale/api/product/${productId}/price/`)
                    .done(function(data) {
                        priceInput.val(data.price);
                        updateCalculations();
                    })
                    .fail(function() {
                        console.error('Failed to fetch product price');
                    });
            } else {
                priceInput.val('');
                updateCalculations();
            }

            if (typeof window.refreshProductListing === 'function') {
                window.refreshProductListing();
            }
        });

        // Calculate totals when inputs change
        $(document).on('input', '.quantity-input, .price-input, .discount-percentage-input, .discount-amount-input, #id_discount, #id_tax, #id_paid, #id_due', function() {
            updateCalculations();
        });

        // When discount percentage changes, update discount amount
        $(document).on('input', '.discount-percentage-input', function() {
            const row = $(this).closest('tr');
            const quantity = parseFloat(row.find('.quantity-input').val()) || 0;
            const unitPrice = parseFloat(row.find('.price-input').val()) || 0;
            const discountPercentage = parseFloat($(this).val()) || 0;

            const subtotal = quantity * unitPrice;
            const discountAmount = (subtotal * discountPercentage) / 100;

            row.find('.discount-amount-input').val(discountAmount.toFixed(2));
            updateCalculations();
        });

        // When discount amount changes, update discount percentage
        $(document).on('input', '.discount-amount-input', function() {
            const row = $(this).closest('tr');
            const quantity = parseFloat(row.find('.quantity-input').val()) || 0;
            const unitPrice = parseFloat(row.find('.price-input').val()) || 0;
            const discountAmount = parseFloat($(this).val()) || 0;

            const subtotal = quantity * unitPrice;
            const discountPercentage = subtotal > 0 ? (discountAmount / subtotal * 100) : 0;

            row.find('.discount-percentage-input').val(discountPercentage.toFixed(2));
            updateCalculations();
        });

        // Handle form submission with action
        $('button[name="action"]').click(function() {
            const action = $(this).val();
            if (action === 'draft') {
                $('#id_status').val('draft');
            } else if (action === 'confirm') {
                $('#id_status').val('confirmed');
            }
        });

        function updateCalculations() {
            let subtotal = 0;

            $('.item-row').each(function() {
                const quantity = parseFloat($(this).find('.quantity-input').val()) || 0;
                const unitPrice = parseFloat($(this).find('.price-input').val()) || 0;
                const discountAmount = parseFloat($(this).find('.discount-amount-input').val()) || 0;

                const rowSubtotal = quantity * unitPrice;
                const total = rowSubtotal - discountAmount;

                $(this).find('.total-price').text('৳' + total.toFixed(2));
                subtotal += total;
            });

            const globalDiscount = parseFloat($('#id_discount').val()) || 0;
            const tax = parseFloat($('#id_tax').val()) || 0;
            const paid = parseFloat($('#id_paid').val()) || 0;
            const grandTotal = subtotal - globalDiscount + tax;
            const due_amount = grandTotal - paid;

            $('#subtotal').text('৳' + subtotal.toFixed(2));
            $('#grand-total').text('৳' + grandTotal.toFixed(2));
            $('#id_due_display').text('৳' + due_amount.toFixed(2));
            $('#id_due').val(due_amount.toFixed(2));
        }

        // Initial calculation
        updateCalculations();

        // Customer Modal Functionality
        $('#add-customer-btn').click(function() {
            $('#customerModal').modal('show');
        });

        $('#saveCustomerBtn').click(function() {
            const form = $('#customerForm');
            const formData = {
                name: $('#customerName').val(),
                phone: $('#customerPhone').val(),
                address: $('#customerAddress').val()
            };

            if (!formData.name.trim()) {
                alert('Customer name is required');
                return;
            }

            $(this).prop('disabled', true).text('Saving...');

            $.ajax({
                url: '/people/customers/create-ajax/',
                type: 'POST',
                data: formData,
                headers: {
                    'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
                },
                success: function(response) {
                    if (response.success) {
                        const customerSelect = $('#id_customer');
                        const newOption = new Option(response.customer.name, response.customer.id, true, true);
                        customerSelect.append(newOption).trigger('change');

                        $('#customerModal').modal('hide');
                        form[0].reset();

                        Swal.fire({
                            title: 'Success',
                            text: 'Customer created successfully',
                            icon: 'success',
                            confirmButtonText: 'OK'
                        });
                    } else {
                        alert('Error creating customer: ' + (response.message || 'Unknown error'));
                    }
                },
                error: function(xhr, status, error) {
                    console.error('Error creating customer:', error);
                    alert('Error creating customer. Please try again.');
                },
                complete: function() {
                    $('#saveCustomerBtn').prop('disabled', false).text('Save Customer');
                }
            });
        });

        $('#customerModal').on('hidden.bs.modal', function () {
            $('#customerForm')[0].reset();
            $('#saveCustomerBtn').prop('disabled', false).text('Save Customer');
        });
    });

    // Delete button handler
    document.querySelectorAll('.delete-btn').forEach(function(element) {
        element.addEventListener('click', function(e) {
            e.preventDefault();
            const url = this.getAttribute('data-url');
            Swal.fire({
                title: 'Are you sure?',
                text: "You won't be able to revert this!",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#3085d6',
                cancelButtonColor: '#d33',
                confirmButtonText: 'Yes, delete it!'
            }).then((result) => {
                if (result.isConfirmed) {
                    fetch(url, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                            'Content-Type': 'application/json'
                        }
                    }).then(response => {
                        if (response.ok) {
                            Swal.fire({
                                title: 'Deleted!',
                                icon: 'success'
                            }).then(() => {
                                window.location.reload();
                            });
                        } else {
                            Swal.fire({
                                title: 'Error!',
                                icon: 'error',
                                confirmButtonText: 'OK'
                            });
                        }
                    });
                }
            });
        });
    });
})();
