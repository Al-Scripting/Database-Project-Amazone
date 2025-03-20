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

    const modalCartBtn = document.getElementById("modal-add-to-cart");
    modalCartBtn.onclick = function () {
        addToCart(id, quantityInput.value);
    };
}


// Close modal
function closeModal() {
    const modal = document.getElementById("product-modal");
    modal.classList.remove("show");
}

// Close modal on outside click
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
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            showNotification(data.message, "success");
            document.getElementById(`stock-${productId}`).innerText = data.sold_out ? "Sold Out" : data.new_stock;
            closeModal();
        } else {
            showNotification(data.error, "error");
        }
    })
    .catch(error => {
        console.error("Error:", error);
        showNotification("Failed to connect to the server!", "error");
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
