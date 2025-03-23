function openModal(id, title, description, price, stock, image) {
    const modal = document.getElementById("product-modal");
    modal.classList.add("show");

    document.getElementById("modal-image").src = image;
    document.getElementById("modal-title").innerText = title;
    document.getElementById("modal-description").innerText = description;
    document.getElementById("modal-price").innerText = `$${price}`;
    document.getElementById("modal-stock").innerText = stock > 0 ? `Stock: ${stock}` : "Sold Out";

    const quantityInput = document.getElementById("modal-quantity");
    quantityInput.value = 1;
    quantityInput.max = stock;
    quantityInput.disabled = stock === 0;

    const modalCartBtn = document.getElementById("modal-add-to-cart");
    modalCartBtn.disabled = stock === 0;
    modalCartBtn.onclick = function () {
        if (stock > 0) {
            addToCart(id, quantityInput.value);
        }
    };
}

function closeModal() {
    const modal = document.getElementById("product-modal");
    modal.classList.remove("show");

    // Remove error class if present
    const qtyInput = document.getElementById("modal-quantity");
    if (qtyInput) qtyInput.classList.remove("input-error");
}

document.addEventListener("click", function (event) {
    const modal = document.getElementById("product-modal");
    if (event.target === modal) {
        closeModal();
    }
});

function addToCart(productId, quantity) {
    fetch(`/add_to_cart/${productId}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest"
        },
        body: `quantity=${quantity}`
    })
    .then(async (response) => {
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
            const data = await response.json();
            const qtyInput = document.getElementById("modal-quantity");
            if (qtyInput) qtyInput.classList.remove("input-error");

            if (data.error) {
                showNotification(data.error, "error");
                if (qtyInput) qtyInput.classList.add("input-error");
                return;
            }

            if (data.message) {
                showNotification(data.message, "success");

                const stockElement = document.getElementById(`stock-${productId}`);
                if (data.sold_out) {
                    if (stockElement) stockElement.innerText = "Sold Out";
                    document.getElementById("modal-stock").innerText = "Sold Out";

                    const modalQty = document.getElementById("modal-quantity");
                    const modalBtn = document.getElementById("modal-add-to-cart");
                    if (modalQty) {
                        modalQty.disabled = true;
                        modalQty.value = 0;
                    }
                    if (modalBtn) modalBtn.disabled = true;

                    const card = stockElement.closest(".product-card");
                    if (card) {
                        const cardBtn = card.querySelector(".add-to-cart");
                        const cardQty = card.querySelector("input[name='quantity']");
                        if (cardBtn) {
                            cardBtn.disabled = true;
                            cardBtn.innerText = "Sold Out";
                        }
                        if (cardQty) {
                            cardQty.disabled = true;
                            cardQty.value = 0;
                        }
                    }
                } else {
                    document.getElementById(`stock-${productId}`).innerText = `Stock: ${data.new_stock}`;
                    document.getElementById("modal-stock").innerText = `Stock: ${data.new_stock}`;
                }

                closeModal();
            }
        } else {
            showNotification("Unexpected server response. Please try again later.", "error");
        }
    })
    .catch(error => {
        console.error("Add to cart failed:", error);
        showNotification("Connection error. Please try again later.", "error");
    });
}



function showNotification(message, type = "success") {
    const container = document.getElementById("notification-container");
    const notification = document.createElement("div");

    notification.className = `notification ${type}`;
    notification.innerText = message;

    container.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Optional restock hook if you use it
function restockAll() {
    fetch('/restock', {
        method: 'POST'
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            for (const [itemId, newStock] of Object.entries(data.updatedStocks)) {
                const stockSpan = document.getElementById(`stock-${itemId}`);
                if (stockSpan) stockSpan.textContent = newStock;

                const modalStockSpan = document.getElementById(`modal-stock-${itemId}`);
                if (modalStockSpan) modalStockSpan.textContent = newStock;
            }

            showNotification("Items restocked!", "success");
        } else {
            showNotification("Restock failed.", "error");
        }
    });
}
