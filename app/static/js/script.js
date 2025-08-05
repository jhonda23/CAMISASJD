// --- carrito persistente ---
const CART_KEY = 'selectstyle_cart';

function getCart() {
  return JSON.parse(localStorage.getItem(CART_KEY) || '[]');
}

function saveCart(cart) {
  localStorage.setItem(CART_KEY, JSON.stringify(cart));
}

function addToCart(product) {
  const cart = getCart();
  const existing = cart.find(p => p.id === product.id);
  if (existing) {
    existing.quantity += 1;
  } else {
    cart.push({ ...product, quantity: 1 });
  }
  saveCart(cart);
  renderCart();
}

function removeFromCart(id) {
  let cart = getCart();
  cart = cart.filter(p => p.id !== id);
  saveCart(cart);
  renderCart();
}

function changeQuantity(id, delta) {
  const cart = getCart();
  const item = cart.find(p => p.id === id);
  if (!item) return;
  item.quantity = Math.max(1, item.quantity + delta);
  saveCart(cart);
  renderCart();
}

function clearCart() {
  localStorage.removeItem(CART_KEY);
  renderCart();
}

function getTotal() {
  const cart = getCart();
  return cart.reduce((sum, p) => sum + parseFloat(p.price) * p.quantity, 0);
}

function renderCart() {
  const cartEl = document.getElementById('cart');
  const itemsEl = document.getElementById('cart-items');
  const countEl = document.getElementById('cart-count');
  const totalEl = document.getElementById('cart-total-amount');

  const cart = getCart();
  itemsEl.innerHTML = '';
  countEl.textContent = cart.reduce((c, p) => c + p.quantity, 0);

  if (cart.length === 0) {
    itemsEl.innerHTML = '<p>El carrito está vacío.</p>';
  } else {
    cart.forEach(p => {
      const div = document.createElement('div');
      div.className = 'cart-item';
      div.innerHTML = `
        <img src="${p.image.startsWith('http') ? p.image : '/static/uploads/' + p.image}" alt="${p.name}">
        <div class="cart-item-info">
          <h4>${p.name}</h4>
          <div class="qty">
            <button data-id="${p.id}" class="dec">-</button>
            <span>${p.quantity}</span>
            <button data-id="${p.id}" class="inc">+</button>
          </div>
          <div>${p.quantity} x $${parseFloat(p.price).toFixed(2)}</div>
          <a href="#" data-id="${p.id}" class="remove" style="color:#d32f2f; font-size:0.8rem;">Eliminar</a>
        </div>
      `;
      itemsEl.appendChild(div);
    });
  }

  totalEl.textContent = `$${getTotal().toFixed(2)}`;
  // listeners
  document.querySelectorAll('.dec').forEach(btn => {
    btn.onclick = e => {
      const id = parseInt(e.target.dataset.id);
      changeQuantity(id, -1);
    };
  });
  document.querySelectorAll('.inc').forEach(btn => {
    btn.onclick = e => {
      const id = parseInt(e.target.dataset.id);
      changeQuantity(id, 1);
    };
  });
  document.querySelectorAll('.remove').forEach(a => {
    a.onclick = e => {
      e.preventDefault();
      const id = parseInt(e.target.dataset.id);
      removeFromCart(id);
    };
  });
}

// --- integración con productos ---
let products = [];
let currentColor = '';
let currentSort = 'default';

async function loadProducts() {
  try {
    const res = await fetch('/products');
    products = await res.json();
    render();
    renderCart();
  } catch (e) {
    console.error('Error cargando productos:', e);
  }
}

function render() {
  const container = document.getElementById('productList');
  container.innerHTML = '';
  let filtered = products.filter(p => !currentColor || p.color === currentColor);

  if (currentSort === 'price-asc') {
    filtered.sort((a,b)=> parseFloat(a.price) - parseFloat(b.price));
  } else if (currentSort === 'price-desc') {
    filtered.sort((a,b)=> parseFloat(b.price) - parseFloat(a.price));
  }

  filtered.forEach(p => {
    const tmpl = document.getElementById('product-card-template');
    const card = tmpl.content.cloneNode(true);
    const wrapper = card.querySelector('.product-card');

    if (p.sold_out) wrapper.classList.add('sold-out');
    const imgEl = card.querySelector('.image-wrapper img');
    imgEl.src = p.image ? `/static/uploads/${p.image}` : 'https://via.placeholder.com/300x380?text=No+Image';
    card.querySelector('.name').textContent = p.name;
    card.querySelector('.price-current').textContent = `$${parseFloat(p.price).toFixed(2)}`;
    if (p.old_price) {
      card.querySelector('.price-old').textContent = `$${parseFloat(p.old_price).toFixed(2)}`;
      card.querySelector('.discount').textContent = p.discount || '';
    } else {
      card.querySelector('.price-old').remove();
      card.querySelector('.discount').remove();
    }
    if (p.sold_out) {
      card.querySelector('.sold-out-label').style.display = 'block';
    }

    // botón comprar
    const buyBtn = card.querySelector('.buy-btn');
    buyBtn.onclick = () => {
      if (p.sold_out) return;
      addToCart({
        id: p.id,
        name: p.name,
        price: p.price,
        image: p.image,
        sold_out: p.sold_out
      });
    };

    container.appendChild(card);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  loadProducts();

  document.querySelectorAll('.color-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      currentColor = btn.dataset.color;
      render();
    });
  });

  document.getElementById('sortSelect').addEventListener('change', e => {
    currentSort = e.target.value;
    render();
  });

  document.getElementById('searchInput').addEventListener('input', e => {
    const q = e.target.value.toLowerCase();
    render(); // re-render with existing color/sort
    const container = document.getElementById('productList');
    container.querySelectorAll('.product-card').forEach(card => {
      const name = card.querySelector('.name').textContent.toLowerCase();
      if (!name.includes(q)) card.style.display = 'none';
    });
  });

  // carrito toggle
  document.getElementById('cart-toggle').addEventListener('click', () => {
    document.getElementById('cart').classList.add('open');
  });
  document.getElementById('cart-close').addEventListener('click', () => {
    document.getElementById('cart').classList.remove('open');
  });
  document.getElementById('clear-cart').addEventListener('click', () => {
    clearCart();
  });
});
