// Wait for DOM to load
document.addEventListener('DOMContentLoaded', function() {
    // Login Form Handler
    const loginForm = document.getElementById('loginform');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    // Signup Form Handler
    const signupForm = document.getElementById('signup-form');
    if (signupForm) {
        signupForm.addEventListener('submit', handleSignup);
    }
});

// Login Function
async function handleLogin(e) {
    e.preventDefault();
    const form = e.target;
    const email = form.email.value.trim().toLowerCase();
    const password = form.password.value;
    const errorElement = document.getElementById('errorMessage');

    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Login failed');
        }

        if (data.success) {
            localStorage.setItem('currentUser', JSON.stringify(data.user));
            window.location.href = '/';
        } else {
            errorElement.textContent = data.message || 'Invalid credentials';
            form.password.value = '';
        }
    } catch (error) {
        console.error('Login error:', error);
        errorElement.textContent = error.message || 'Login failed. Please try again.';
    }
}

// Signup Function
async function handleSignup(e) {
    e.preventDefault();
    const form = e.target;
    const fullname = form.fullname.value.trim();
    const email = form.email.value.trim().toLowerCase();
    const password = form.password.value;
    const confirmPassword = form['confirm-password'].value;
    const errorElement = document.getElementById('errorMessage');

    // Clear previous errors
    errorElement.textContent = '';

    // Validation
    if (!fullname || !email || !password || !confirmPassword) {
        errorElement.textContent = 'All fields are required!';
        return;
    }

    if (password.length < 8) {
        errorElement.textContent = 'Password must be at least 8 characters!';
        return;
    }

    if (password !== confirmPassword) {
        errorElement.textContent = 'Passwords do not match!';
        form.password.value = '';
        form['confirm-password'].value = '';
        return;
    }

    try {
        const response = await fetch('/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ fullname, email, password })
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Signup failed');
        }

        if (data.success) {
            alert('Signup successful! Redirecting to login...');
            setTimeout(() => window.location.href = '/login', 1000);
        } else {
            errorElement.textContent = data.message || 'Signup failed';
        }
    } catch (error) {
        console.error('Signup error:', error);
        errorElement.textContent = error.message || 'Signup failed. Please try again.';
    }
}

// Logout Function
function logout() {
    if (confirm('Are you sure you want to logout?')) {
        fetch('/logout', { method: 'GET' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    localStorage.removeItem('currentUser');
                    window.location.href = '/login';
                } else {
                    alert('Logout failed. Please try again.');
                }
            })
            .catch(error => {
                console.error('Logout error:', error);
                alert('Logout failed. Please try again.');
            });
    }
}