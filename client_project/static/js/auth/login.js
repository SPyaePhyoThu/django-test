

export default () => ({
    email: '',
    password: '',
    errors: { email: null, password: null, form: null },
    isLoading: false,
    async login() {
        this.isLoading = true;
        this.errors = { email: null, password: null, form: null };
        try {
            const response = await fetch('/auth/api/login/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.$store.getCookie('csrftoken')
                },
                body: JSON.stringify({ email: this.email, password: this.password })
            });
            const data = await response.json();
            if (response.ok) {
                window.location.href = '/auth/coming-soon/';
            } else {
                if (response.status === 401 && data.message) {
                    this.errors.form = data.message;
                } else if (response.status === 400) {
                    this.errors.email = data.email ? data.email.join(' ') : null;
                    this.errors.password = data.password ? data.password.join(' ') : null;
                } else {
                    this.errors.form = 'An unknown error occurred. Please try again.';
                }
            }
        } catch (error) {
            this.errors.form = 'An error occurred while connecting to the server.';
        } finally {
            this.isLoading = false;
        }
    }
});
