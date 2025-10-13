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
            updateDeleteButtonVisibility();
        });

        // Remove item row
        $(document).on('click', '.remove-item', function() {
            $(this).closest('tr').remove();
            updateCalculations();
            updateDeleteButtonVisibility();
            if (typeof window.refreshProductListing === 'function') {
                window.refreshProductListing();
            }
        });

        // Handle DELETE checkbox changes for existing items
        $(document).on('change', 'input[name*="DELETE"]', function() {
            updateDeleteButtonVisibility();
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

        function updateDeleteButtonVisibility() {
            // Count only rows that are not marked for deletion
            let activeRowCount = 0;
            $('.item-row').each(function() {
                const deleteCheckbox = $(this).find('input[name*="DELETE"]');
                // If there's no DELETE checkbox or it's not checked, count this row
                if (deleteCheckbox.length === 0 || !deleteCheckbox.is(':checked')) {
                    activeRowCount++;
                }
            });

            if (activeRowCount === 1) {
                // Hide delete buttons only for rows that are not marked for deletion
                $('.item-row').each(function() {
                    const deleteCheckbox = $(this).find('input[name*="DELETE"]');
                    if (deleteCheckbox.length === 0 || !deleteCheckbox.is(':checked')) {
                        $(this).find('.remove-item').hide();
                        $(this).find('label[for*="DELETE"]').hide();
                    }
                });
            } else {
                // Show all delete buttons
                $('.item-row .remove-item').show();
                $('.item-row label[for*="DELETE"]').show();
            }
        }

        // Initial calculation
        updateCalculations();
        updateDeleteButtonVisibility();

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



        // Product listing modal
        
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



$(document).ready(function() {
    let productsData = [];
    let totalProducts = 0;
    let currentPage = 1;
    const productsPerPage = 12;

    // Load initial data
    loadFilters();
    loadProducts();

    // Load filter options
    function loadFilters() {
        // Load categories
        $.get('/product/api/categories/', function(categories) {
            const categoryFilter = $('#category-filter');
            categories.forEach(function(cat) {
                categoryFilter.append(`<option value="${cat.id}">${cat.name}</option>`);
            });
        });

        // Load brands
        $.get('/product/api/brands/', function(brands) {
            const brandFilter = $('#brand-filter');
            brands.forEach(function(brand) {
                brandFilter.append(`<option value="${brand.id}">${brand.name}</option>`);
            });
        });
    }

    // Load products with server-side pagination
    function loadProducts(filters = {}, page = 1) {
        // Show loading state
        $('#product-grid').html(`
            <div class="no-products">
                <i class="fas fa-spinner fa-spin fa-2x"></i>
                <p class="mt-2">Loading products...</p>
            </div>
        `);

        // Add pagination parameters
        const params = {
            ...filters,
            page: page,
            page_size: productsPerPage
        };

        $.ajax({
            url: '/product/api/products/',
            type: 'GET',
            data: params,
            success: function(response) {
                // Handle both paginated and non-paginated responses
                if (response.results !== undefined) {
                    // Paginated response
                    productsData = response.results;
                    totalProducts = response.count || response.results.length;
                } else {
                    // Non-paginated response (fallback)
                    productsData = response;
                    totalProducts = response.length;
                }

                currentPage = page;
                renderProducts();
                updatePaginationInfo();
            },
            error: function() {
                $('#product-grid').html(`
                    <div class="no-products">
                        <i class="fas fa-exclamation-triangle fa-2x text-danger"></i>
                        <p class="mt-2">Failed to load products</p>
                    </div>
                `);
            }
        });
    }

    // Get list of already selected product IDs
    function getSelectedProductIds() {
        const selectedIds = [];
        $('.item-row').each(function() {
            const productSelect = $(this).find('select[name*="product"]');
            const productId = productSelect.val();
            if (productId) {
                selectedIds.push(productId);
            }
        });
        return selectedIds;
    }

    // Render products (server-side pagination - products already paginated)
    function renderProducts() {
        const grid = $('#product-grid');
        grid.empty();

        if (productsData.length === 0) {
            grid.html(`
                <div class="no-products">
                    <i class="fas fa-box-open fa-2x"></i>
                    <p class="mt-2">No products found</p>
                </div>
            `);
            return;
        }

        // Get already selected products
        const selectedProductIds = getSelectedProductIds();

        // Render products (already paginated by server)
        productsData.forEach(function(product) {
            const stockClass = product.stock > 0 ? 'stock-in' : 'stock-out';
            const stockText = product.stock > 0 ? `Stock: ${product.stock}` : 'Out of Stock';

            const imageHtml = product.image
                ? `<img src="${product.image}" alt="${product.name}">`
                : `<div class="no-image">${product.name.charAt(0).toUpperCase()}</div>`;

            // Check if product is already selected
            const isDisabled = selectedProductIds.includes(product.id.toString());
            const disabledClass = isDisabled ? 'disabled' : '';

            const card = $(`
                <div class="product-card ${disabledClass}" data-product-id="${product.id}" data-product-price="${product.price}">
                    <div class="add-icon">
                        <i class="fas fa-plus"></i>
                    </div>
                    <div class="product-image">
                        ${imageHtml}
                    </div>
                    <div class="product-info">
                        <div class="product-name" title="${product.name}">${product.name}</div>
                        ${product.brand ? `<div class="product-brand">${product.brand}</div>` : ''}
                        <div class="product-price">৳${parseFloat(product.price).toFixed(2)}</div>
                        <div class="product-stock ${stockClass}">${stockText}</div>
                    </div>
                </div>
            `);

            grid.append(card);
        });
    }

    // Update pagination info
    function updatePaginationInfo() {
        const startIndex = totalProducts === 0 ? 0 : (currentPage - 1) * productsPerPage + 1;
        const endIndex = Math.min(currentPage * productsPerPage, totalProducts);
        const totalPages = Math.ceil(totalProducts / productsPerPage);

        $('#page-start').text(startIndex);
        $('#page-end').text(endIndex);
        $('#total-products').text(totalProducts);

        // Update button states
        $('#prev-page').prop('disabled', currentPage === 1);
        $('#next-page').prop('disabled', currentPage >= totalPages || totalProducts === 0);
    }

    // Handle product card click
    $(document).on('click', '.product-card', function() {
        // Prevent clicking on disabled cards
        if ($(this).hasClass('disabled')) {
            return;
        }

        const productId = $(this).data('product-id');
        const productPrice = $(this).data('product-price');

        // Add product to the first empty row or create new row
        addProductToSale(productId, productPrice);
    });

    // Add product to sale items
    function addProductToSale(productId, productPrice) {
        // Check if product is already added
        const selectedIds = getSelectedProductIds();
        if (selectedIds.includes(productId.toString())) {
            return; // Product already added, do nothing
        }

        // Find first empty row
        let emptyRow = null;
        $('.item-row').each(function() {
            const productSelect = $(this).find('select[name*="product"]');
            if (!productSelect.val()) {
                emptyRow = $(this);
                return false;
            }
        });

        // If no empty row, create new one
        if (!emptyRow) {
            $('.add-item').first().click();
            // Wait for new row to be added
            setTimeout(function() {
                emptyRow = $('.item-row').last();
                fillProductRow(emptyRow, productId, productPrice);
            }, 100);
        } else {
            fillProductRow(emptyRow, productId, productPrice);
        }
    }

    // Fill product row with data
    function fillProductRow(row, productId, productPrice) {
        const productSelect = row.find('select[name*="product"]');
        const priceInput = row.find('.price-input');
        const quantityInput = row.find('.quantity-input');

        // Set product
        productSelect.val(productId).trigger('change');

        // Set price
        priceInput.val(productPrice);

        // Set default quantity to 1
        if (!quantityInput.val() || quantityInput.val() == 0) {
            quantityInput.val(1);
        }

        // Trigger calculation
        updateCalculations();

        // Refresh product listing to disable the added product
        renderProducts();
    }

    // Expose function globally to be called from form.html
    window.refreshProductListing = function() {
        renderProducts();
    };

    // Store current filters
    let currentFilters = {};

    // Filter products
    function filterProducts() {
        const search = $('#product-search').val().toLowerCase();
        const category = $('#category-filter').val();
        const brand = $('#brand-filter').val();

        currentFilters = {};
        if (search) currentFilters.search = search;
        if (category) currentFilters.category = category;
        if (brand) currentFilters.brand = brand;

        // Reset to page 1 when filters change
        loadProducts(currentFilters, 1);
    }

    // Search input with debounce
    let searchTimeout;
    $('#product-search').on('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(filterProducts, 300);
    });

    // Filter dropdowns
    $('#category-filter, #brand-filter').on('change', filterProducts);

    // Clear filters
    $('#clear-filters').on('click', function() {
        $('#product-search').val('');
        $('#category-filter').val('');
        $('#brand-filter').val('');
        currentFilters = {};
        loadProducts({}, 1);
    });

    // Pagination controls
    $('#prev-page').on('click', function() {
        if (currentPage > 1) {
            loadProducts(currentFilters, currentPage - 1);
        }
    });

    $('#next-page').on('click', function() {
        const totalPages = Math.ceil(totalProducts / productsPerPage);
        if (currentPage < totalPages) {
            loadProducts(currentFilters, currentPage + 1);
        }
    });
});
