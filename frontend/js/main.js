// API Configuration
const API_BASE_URL = '/api';
let authToken = localStorage.getItem('token');
let currentUser = null;

// Get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('Frontend loaded on port 8001');
    checkAuth();
    loadVehicles();
    setupEventListeners();
});

// Setup Event Listeners
function setupEventListeners() {
    // Login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    // Signup form
    const signupForm = document.getElementById('signupForm');
    if (signupForm) {
        signupForm.addEventListener('submit', handleSignup);
    }
    
    // Booking form
    const bookingForm = document.getElementById('bookingForm');
    if (bookingForm) {
        bookingForm.addEventListener('submit', handleBooking);
    }
    
    // Add vehicle form
    const addVehicleForm = document.getElementById('addVehicleForm');
    if (addVehicleForm) {
        addVehicleForm.addEventListener('submit', handleAddVehicle);
    }
    
    // Contact form
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', handleContact);
    }
    
    // Close modals when clicking outside
    window.onclick = function(event) {
        if (event.target.classList && event.target.classList.contains('modal')) {
            event.target.style.display = 'none';
        }
    };
}

// Authentication Functions
function checkAuth() {
    if (authToken) {
        // Fetch user profile
        fetch(`${API_BASE_URL}/accounts/profile/`, {
            headers: {
                'Authorization': `Token ${authToken}`,
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(res => {
            if (res.status === 401) {
                logout();
                return null;
            }
            return res.json();
        })
        .then(data => {
            if (data && !data.detail) {
                currentUser = data;
                updateUIForLoggedInUser();
            }
        })
        .catch(error => {
            console.error('Auth check error:', error);
            logout();
        });
    } else {
        updateUIForLoggedOutUser();
    }
}

function updateUIForLoggedInUser() {
    const navButtons = document.getElementById('navButtons');
    const userMenu = document.getElementById('userMenu');
    const userName = document.getElementById('userName');
    
    if (navButtons) navButtons.style.display = 'none';
    if (userMenu) userMenu.style.display = 'block';
    if (userName && currentUser) userName.textContent = currentUser.username;
    
    // Show owner-specific links if user is vehicle owner
    if (currentUser && currentUser.user_type === 'owner') {
        const ownerVehiclesLink = document.getElementById('ownerVehiclesLink');
        if (ownerVehiclesLink) ownerVehiclesLink.style.display = 'block';
    }
}

function updateUIForLoggedOutUser() {
    const navButtons = document.getElementById('navButtons');
    const userMenu = document.getElementById('userMenu');
    
    if (navButtons) navButtons.style.display = 'flex';
    if (userMenu) userMenu.style.display = 'none';
}

async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/accounts/login/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            credentials: 'include',
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.ok && data.token) {
            authToken = data.token;
            localStorage.setItem('token', authToken);
            currentUser = data.user;
            updateUIForLoggedInUser();
            closeLoginModal();
            showNotification('Login successful!', 'success');
            loadVehicles();
        } else {
            showNotification(data.message || 'Login failed! Invalid credentials', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showNotification('Login failed! Please try again.', 'error');
    }
}

async function handleSignup(e) {
    e.preventDefault();
    const userData = {
        username: document.getElementById('signupUsername').value,
        email: document.getElementById('signupEmail').value,
        password: document.getElementById('signupPassword').value,
        user_type: document.getElementById('signupUserType').value
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/accounts/register/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            credentials: 'include',
            body: JSON.stringify(userData)
        });
        
        const data = await response.json();
        
        if (response.ok && data.token) {
            authToken = data.token;
            localStorage.setItem('token', authToken);
            currentUser = data.user;
            updateUIForLoggedInUser();
            closeSignupModal();
            showNotification('Account created successfully!', 'success');
            loadVehicles();
        } else {
            let errorMsg = 'Signup failed! ';
            if (data.username) errorMsg += 'Username already exists. ';
            if (data.email) errorMsg += 'Email already exists. ';
            showNotification(errorMsg, 'error');
        }
    } catch (error) {
        console.error('Signup error:', error);
        showNotification('Signup failed! Please try again.', 'error');
    }
}

function logout() {
    localStorage.removeItem('token');
    authToken = null;
    currentUser = null;
    updateUIForLoggedOutUser();
    showNotification('Logged out successfully!', 'success');
}

// Vehicle Functions
function loadVehicles() {
    fetch(`${API_BASE_URL}/vehicles/`, {
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        credentials: 'include'
    })
    .then(res => res.json())
    .then(data => {
        displayVehicles(data);
    })
    .catch(error => {
        console.error('Error loading vehicles:', error);
        const grid = document.getElementById('vehiclesGrid');
        if (grid) {
            grid.innerHTML = '<div class="loading">Error loading vehicles. Please refresh.</div>';
        }
    });
}

function displayVehicles(vehicles) {
    const grid = document.getElementById('vehiclesGrid');
    
    if (!grid) return;
    
    if (!vehicles || vehicles.length === 0) {
        grid.innerHTML = '<div class="loading">No vehicles available</div>';
        return;
    }
    
    grid.innerHTML = vehicles.map(vehicle => `
        <div class="vehicle-card" data-vehicle='KSH{JSON.stringify(vehicle)}'>
            <div class="vehicle-image">
                <i class="fas fa-KSH{getVehicleIcon(vehicle.vehicle_type)}"></i>
            </div>
            <div class="vehicle-info">
                <h3>${vehicle.brand} ${vehicle.model}</h3>
                <div class="vehicle-details">
                    <span><i class="fas fa-users"></i> ${vehicle.seating_capacity} seats</span>
                    <span><i class="fas fa-gas-pump"></i> ${vehicle.fuel_type}</span>
                </div>
                <div class="price">KSH${vehicle.price_per_day}/day</div>
                <button class="btn-book" onclick="showBookingModal(KSH{vehicle.id})">Book Now</button>
            </div>
        </div>
    `).join('');
}

function getVehicleIcon(type) {
    const icons = {
        'car': 'car',
        'bike': 'motorcycle',
        'van': 'van-shuttle',
        'truck': 'truck',
        'bus': 'bus'
    };
    return icons[type] || 'car';
}

function filterVehicles() {
    const vehicleType = document.getElementById('vehicleType').value;
    const fuelType = document.getElementById('fuelType').value;
    const maxPrice = document.getElementById('maxPrice').value;
    const search = document.getElementById('searchVehicle').value.toLowerCase();
    
    fetch(`${API_BASE_URL}/vehicles/`)
    .then(res => res.json())
    .then(vehicles => {
        let filtered = vehicles;
        
        if (vehicleType) {
            filtered = filtered.filter(v => v.vehicle_type === vehicleType);
        }
        if (fuelType) {
            filtered = filtered.filter(v => v.fuel_type === fuelType);
        }
        if (maxPrice) {
            filtered = filtered.filter(v => v.price_per_day <= parseInt(maxPrice));
        }
        if (search) {
            filtered = filtered.filter(v => 
                v.brand.toLowerCase().includes(search) || 
                v.model.toLowerCase().includes(search)
            );
        }
        
        displayVehicles(filtered);
    });
}

// Booking Functions
let currentBookingVehicle = null;

function showBookingModal(vehicleId) {
    if (!authToken) {
        showNotification('Please login to book a vehicle', 'error');
        showLoginModal();
        return;
    }
    
    fetch(`${API_BASE_URL}/vehicles/${vehicleId}/`)
    .then(res => res.json())
    .then(vehicle => {
        currentBookingVehicle = vehicle;
        const vehicleInfo = document.getElementById('bookingVehicleInfo');
        if (vehicleInfo) {
            vehicleInfo.innerHTML = `
                <div class="vehicle-info">
                    <h3>${vehicle.brand} ${vehicle.model}</h3>
                    <p>Price: $KSH{vehicle.price_per_day}/day</p>
                    <p>Seats: ${vehicle.seating_capacity}</p>
                </div>
            `;
        }
        document.getElementById('bookingModal').style.display = 'block';
        
        // Set min dates
        const today = new Date().toISOString().split('T')[0];
        const startDate = document.getElementById('startDate');
        const endDate = document.getElementById('endDate');
        
        if (startDate) startDate.min = today;
        if (endDate) endDate.min = today;
        
        // Add date change listeners
        if (startDate) startDate.onchange = calculatePrice;
        if (endDate) endDate.onchange = calculatePrice;
    });
}

function calculatePrice() {
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    const priceCalculation = document.getElementById('priceCalculation');
    
    if (startDate && endDate && currentBookingVehicle) {
        const start = new Date(startDate);
        const end = new Date(endDate);
        const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24));
        
        if (days > 0) {
            const total = days * currentBookingVehicle.price_per_day;
            if (priceCalculation) {
                priceCalculation.innerHTML = `
                    <div class="price-calculation">
                        <p>Days: KSH{days}</p>
                        <p>Total Price: KSH KSH{total}</p>
                    </div>
                `;
            }
        } else if (priceCalculation) {
            priceCalculation.innerHTML = '<p style="color: red;">End date must be after start date</p>';
        }
    }
}

async function handleBooking(e) {
    e.preventDefault();
    
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    
    if (!startDate || !endDate) {
        showNotification('Please select dates', 'error');
        return;
    }
    
    const bookingData = {
        vehicle: currentBookingVehicle.id,
        start_date: startDate + 'T10:00:00',
        end_date: endDate + 'T10:00:00'
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/bookings/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Token ${authToken}`,
                'X-CSRFToken': getCookie('csrftoken')
            },
            credentials: 'include',
            body: JSON.stringify(bookingData)
        });
        
        const data = await response.json();
        
        if (response.ok && data.id) {
            showNotification('Booking created successfully!', 'success');
            closeBookingModal();
        } else {
            showNotification(data.message || 'Booking failed!', 'error');
        }
    } catch (error) {
        console.error('Booking error:', error);
        showNotification('Booking failed!', 'error');
    }
}

// Modal Functions
function showLoginModal() {
    const modal = document.getElementById('loginModal');
    if (modal) modal.style.display = 'block';
}

function closeLoginModal() {
    const modal = document.getElementById('loginModal');
    if (modal) modal.style.display = 'none';
}

function showSignupModal() {
    const modal = document.getElementById('signupModal');
    if (modal) modal.style.display = 'block';
}

function closeSignupModal() {
    const modal = document.getElementById('signupModal');
    if (modal) modal.style.display = 'none';
}

function closeBookingModal() {
    const modal = document.getElementById('bookingModal');
    if (modal) modal.style.display = 'none';
}

function closeProfileModal() {
    const modal = document.getElementById('profileModal');
    if (modal) modal.style.display = 'none';
}

function closeBookingsModal() {
    const modal = document.getElementById('bookingsModal');
    if (modal) modal.style.display = 'none';
}

function closeMyVehiclesModal() {
    const modal = document.getElementById('myVehiclesModal');
    if (modal) modal.style.display = 'none';
}

function closeAddVehicleModal() {
    const modal = document.getElementById('addVehicleModal');
    if (modal) modal.style.display = 'none';
}

function scrollToVehicles() {
    document.getElementById('vehicles').scrollIntoView({ behavior: 'smooth' });
}

function showMyVehicles() {
    // This function will be implemented if needed
    console.log('Show my vehicles');
}

function showAddVehicleForm() {
    const modal = document.getElementById('addVehicleModal');
    if (modal) modal.style.display = 'block';
}

function handleAddVehicle(e) {
    e.preventDefault();
    showNotification('Vehicle added successfully!', 'success');
}

function handleContact(e) {
    e.preventDefault();
    showNotification('Message sent successfully!', 'success');
    e.target.reset();
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        padding: 1rem;
        background: ${type === 'success' ? '#4caf50' : '#f44336'};
        color: white;
        border-radius: 5px;
        z-index: 3000;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Add notification animation styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .booking-card {
        border: 1px solid #ddd;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    
    .status-pending {
        color: orange;
        font-weight: bold;
    }
    
    .status-confirmed {
        color: green;
        font-weight: bold;
    }
    
    .status-cancelled {
        color: red;
        font-weight: bold;
    }
    
    .status-completed {
        color: blue;
        font-weight: bold;
    }
    
    .price-calculation {
        background: #f0f0f0;
        padding: 1rem;
        border-radius: 5px;
        margin-top: 1rem;
    }
`;
document.head.appendChild(style);
