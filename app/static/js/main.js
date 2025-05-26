// Mobile menu toggle
document.getElementById('nav-toggle').addEventListener('click', () => {
    document.getElementById('nav-content').classList.toggle('hidden');
});

// Modal handling (Specific for security-modal, general modal closing removed)
const securityModal = document.getElementById('security-modal'); // Assuming you have a security-modal

// Function to show a specific modal
const showModal = (modalId) => {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
    }
};

// Function to hide a specific modal
const hideModal = (modalId) => {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
};

// Close security modal on click outside its content
if (securityModal) {
    securityModal.addEventListener('click', (e) => {
        // Only close if the click is directly on the modal backdrop
        if (e.target === securityModal) {
            hideModal('security-modal');
        }
    });
}

// Close security modal on escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        if (securityModal && securityModal.style.display === 'flex') {
            hideModal('security-modal');
        }
        // No need to close PDF viewer here, as it has its own listener
    }
});


// Security protocol modal trigger
const showSecurityButton = document.getElementById('show-security');
if (showSecurityButton) {
    showSecurityButton.addEventListener('click', () => {
        showModal('security-modal');
    });
}


// Subscribe to push notifications
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.ready.then(registration => {
        registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array('{{ current_app.config["VAPID_PUBLIC_KEY"] }}')
        }).then(subscription => {
            // Send subscription to server
            fetch('/subscribe', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(subscription)
            });
        });.catch(err => {
             console.error('Failed to subscribe:', err);
});
}

// Helper function
function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding)
        .replace(/-/g, '+')
        .replace(/_/g, '/');
    const rawData = atob(base64);
    return Uint8Array.from([...rawData].map(char => char.charCodeAt(0)));
}
