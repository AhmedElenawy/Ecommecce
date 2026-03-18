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
    
    if (this.isSearch && this.lastCursor) {
      // For search results, lastCursor is actually a page number
      this.currentPage = parseInt(this.lastCursor) || 2;
      this.paginationType = 'offset';
    }
    
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
    const params = new URLSearchParams();
    
    // Always request list_only format
    params.append('list_only', 'true');

    // Add pagination parameter based on detected type
    if (this.paginationType === 'offset') {
      // For search (offset-based pagination), use page number
      params.append('page', this.currentPage);
      console.log('Search pagination: requesting page', this.currentPage);
    } else {
      // For regular listings (cursor-based pagination)
      if (this.lastCursor) {
        params.append('cursor', this.lastCursor);
        console.log('Cursor pagination: requesting cursor', this.lastCursor);
      }
    }

    // Add filter parameters if present
    if (window.paginationData.category) {
      params.append('category', window.paginationData.category);
    }
    if (window.paginationData.tags) {
      params.append('tags', window.paginationData.tags);
    }
    if (window.paginationData.query) {
      params.append('query', window.paginationData.query);
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
   * The response should contain pagination data in the HTML
   */
  updatePaginationState(html) {
    // Extract pagination data from response
    const paginationData = this.extractPaginationData(html);
    
    if (paginationData) {
      this.hasMore = paginationData.hasNext;
      
      if (this.paginationType === 'offset') {
        // For offset-based pagination, increment page number
        if (paginationData.nextPage) {
          this.currentPage = paginationData.nextPage;
        } else if (paginationData.page) {
          this.currentPage = paginationData.page + 1;
        } else {
          this.currentPage += 1;
        }
        console.log('Updated page to:', this.currentPage);
      } else {
        // For cursor-based pagination, update cursor
        if (paginationData.lastCursor && typeof paginationData.lastCursor === 'string') {
          this.lastCursor = paginationData.lastCursor;
          console.log('Updated cursor to:', this.lastCursor);
        }
      }
    }

    if (!this.hasMore) {
      this.showNoMoreProducts();
    }
  }

  /**
   * Extract pagination data from HTML response
   * Looks for a script tag or data attribute containing pagination info
   */
  extractPaginationData(html) {
    // Method 1: Look for JSON script tag with pagination data
    const jsonScriptMatch = html.match(/<script[^>]*type=["\']application\/json["\']\s*id=["\']pagination-data["\']\s*[^>]*>[\s\S]*?({[\s\S]*?})[\s\S]*?<\/script>/);
    if (jsonScriptMatch) {
      try {
        const data = JSON.parse(jsonScriptMatch[1]);
        return {
          hasNext: data.hasNext,
          lastCursor: data.lastCursor
        };
      } catch (e) {
        console.warn('Could not parse pagination data from JSON script', e);
      }
    }

    // Method 2: Look for a window.paginationData script tag
    const scriptMatch = html.match(/<script[^>]*>[\s\S]*?window\.paginationData\s*=\s*({[\s\S]*?});[\s\S]*?<\/script>/);
    if (scriptMatch) {
      try {
        return eval('(' + scriptMatch[1] + ')');
      } catch (e) {
        console.warn('Could not parse pagination data from script', e);
      }
    }

    // Method 3: Look for data attributes
    const temp = document.createElement('div');
    temp.innerHTML = html;
    const firstProduct = temp.querySelector('[data-pagination-info]');
    if (firstProduct) {
      try {
        return JSON.parse(firstProduct.getAttribute('data-pagination-info'));
      } catch (e) {
        console.warn('Could not parse pagination data from attribute', e);
      }
    }

    // If we can't find pagination data, assume we've reached the end
    return { hasNext: false };
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
