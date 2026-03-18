/**
 * Infinite Scroll Pagination Handler
 * Supports both cursor-based and offset-based pagination
 * Automatically detects pagination type from view response
 */

class PaginationManager {
  constructor() {
    this.isLoading = false;
    this.hasMore = window.paginationData?.hasNext || false;
    this.lastCursor = window.paginationData?.lastCursor || null;
    this.currentPage = 1;
    this.paginationType = 'cursor'; // default to cursor-based
    
    // Detect if this is a search (offset-based) or regular listing (cursor-based)
    this.isSearch = (window.paginationData?.query && window.paginationData.query.trim() !== '') ? true : false;
    
    this.containerSelector = '#products-container';
    this.sentinelSelector = '#pagination-sentinel';
    this.loadingSpinnerSelector = '#loading-spinner';
    this.noMoreProductsSelector = '#no-more-products';
    
    this.init();
  }

  /**
   * Initialize the pagination manager
   */
  init() {
    this.setupIntersectionObserver();
    this.setupEventListeners();
  }

  /**
   * Setup Intersection Observer for infinite scroll
   */
  setupIntersectionObserver() {
    const sentinel = document.querySelector(this.sentinelSelector);
    
    if (!sentinel) {
      console.warn('Pagination sentinel element not found');
      return;
    }

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting && this.hasMore && !this.isLoading) {
          this.loadMoreProducts();
        }
      });
    }, {
      threshold: 0.1,
      rootMargin: '50px'
    });

    observer.observe(sentinel);
  }

  /**
   * Setup event listeners for manual pagination (if needed)
   */
  setupEventListeners() {
    // Listen for back button to reset pagination
    window.addEventListener('popstate', () => {
      location.reload();
    });
  }

  /**
   * Load more products based on current pagination type
   */
  async loadMoreProducts() {
    if (this.isLoading || !this.hasMore) return;

    this.isLoading = true;
    this.showLoadingSpinner();

    try {
      const html = await this.fetchNextPage();
      this.appendProducts(html);
    } catch (error) {
      console.error('Error loading more products:', error);
      this.showErrorMessage('Failed to load more products. Please try again.');
    } finally {
      this.isLoading = false;
      this.hideLoadingSpinner();
    }
  }

  /**
   * Fetch the next page of products from the server
   */
  async fetchNextPage() {
    const params = this.buildQueryParams();
    const url = this.buildUrl(params);

    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const html = await response.text();
    return html;
  }

  /**
   * Build query parameters for the request
   */
  buildQueryParams() {
    // Start with current URL parameters to preserve ALL existing filters
    const params = new URLSearchParams(window.location.search);
    
    // Always request list_only format
    params.set('list_only', 'true');

    // Add pagination parameter based on detected type
    if (this.paginationType === 'offset') {
      // For search (offset-based pagination), use page number
      params.set('page', this.currentPage);
    } else {
      // For regular listings (cursor-based pagination)
      if (this.lastCursor) {
        params.set('cursor', this.lastCursor);
      } else {
        params.delete('cursor');
      }
    }

    // Get all current filter form values and update params
    const filterForm = document.getElementById('filters-form');
    if (filterForm) {
      const formElements = filterForm.querySelectorAll('input, select');
      
      // First, clear any existing filter parameters that might have changed
      const filterParamNames = ['low_price', 'max_price', 'category', 'tags', 'in_stock'];
      filterParamNames.forEach(param => {
        params.delete(param);
      });
      
      // Now add the current filter form values
      formElements.forEach((element) => {
        // Skip pagination-related fields
        if (['list_only', 'page', 'cursor'].includes(element.name)) {
          return;
        }
        
        // Handle checkboxes
        if (element.type === 'checkbox') {
          if (element.checked) {
            params.append(element.name, element.value || 'true');
          }
        }
        // Handle select with multiple values
        else if (element.tagName === 'SELECT' && element.multiple) {
          Array.from(element.selectedOptions).forEach(option => {
            params.append(element.name, option.value);
          });
        }
        // Handle other inputs and selects
        else if (element.value && element.name) {
          params.append(element.name, element.value);
        }
      });
    }

    return params;
  }

  /**
   * Build the URL for the fetch request
   */
  buildUrl(params) {
    let path = window.location.pathname;
    
    // Ensure path ends without trailing slash for consistency
    if (path.endsWith('/')) {
      path = path.slice(0, -1);
    }

    return `${path}/?${params.toString()}`;
  }

  /**
   * Append fetched products to the container
   */
  appendProducts(html) {
    const container = document.querySelector(this.containerSelector);
    if (!container) {
      console.error('Products container not found');
      return;
    }

    // Create a temporary container to parse the HTML
    const temp = document.createElement('div');
    temp.innerHTML = html;

    // Extract products from the response
    const newProducts = temp.querySelectorAll('[data-product-id]');
    
    if (newProducts.length === 0) {
      // No more products
      this.hasMore = false;
      this.showNoMoreProducts();
      return;
    }

    // Append new products to container
    newProducts.forEach((product) => {
      container.appendChild(product.cloneNode(true));
    });

    // Update pagination state from response
    this.updatePaginationState(html);

    // Trigger any animations (e.g., AOS)
    if (window.AOS) {
      AOS.refresh();
    }
  }

  /**
   * Update pagination state based on server response
   */
  updatePaginationState(html) {
    // Extract pagination data from response
    const paginationData = this.extractPaginationData(html);
    
    if (paginationData) {
      this.hasMore = paginationData.hasNext;
      
      if (this.paginationType === 'offset') {
        // For offset-based pagination
        if (paginationData.nextPage) {
          this.currentPage = paginationData.nextPage;
        } else if (paginationData.page) {
          this.currentPage = paginationData.page + 1;
        } else {
          this.currentPage += 1;
        }
      } else {
        // For cursor-based pagination
        if (paginationData.lastCursor) {
          this.lastCursor = paginationData.lastCursor;
        }
      }
    }

    if (!this.hasMore) {
      this.showNoMoreProducts();
    }
  }

  /**
   * Extract pagination data from HTML response
   * Looks for the hidden data div we added in product_list_only.html
   */
  extractPaginationData(html) {
    // Create a temporary container to parse the HTML
    const temp = document.createElement('div');
    temp.innerHTML = html;

    // Find the metadata div
    const metaDiv = temp.querySelector('#pagination-meta-data');

    if (metaDiv) {
      return {
        hasNext: metaDiv.getAttribute('data-has-next') === 'true',
        lastCursor: metaDiv.getAttribute('data-last-cursor')
      };
    }

    // Fallback: If we can't find metadata, assume we've reached the end
    return { hasNext: false, lastCursor: null };
  }

  /**
   * Show loading spinner
   */
  showLoadingSpinner() {
    const spinner = document.querySelector(this.loadingSpinnerSelector);
    if (spinner) {
      spinner.classList.add('visible');
    }
  }

  /**
   * Hide loading spinner
   */
  hideLoadingSpinner() {
    const spinner = document.querySelector(this.loadingSpinnerSelector);
    if (spinner) {
      spinner.classList.remove('visible');
    }
  }

  /**
   * Show "no more products" message
   */
  showNoMoreProducts() {
    const noMore = document.querySelector(this.noMoreProductsSelector);
    if (noMore) {
      noMore.classList.add('visible');
    }
  }

  /**
   * Show error message
   */
  showErrorMessage(message) {
    console.error(message);
    const noMore = document.querySelector(this.noMoreProductsSelector);
    if (noMore) {
      noMore.textContent = message;
      noMore.classList.add('visible');
    }
  }
}

// Initialize pagination manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  new PaginationManager();
});