

export default () => ({
    username: '',
    email: '',
    password: '',
    errors: { username: null, email: null, password: null, form: null },
    isLoading: false,
    async register() {
        this.isLoading = true;
        this.errors = { username: null, email: null, password: null, form: null };
        try {
            const response = await fetch('/auth/api/register/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.$store.getCookie('csrftoken')
                },
                body: JSON.stringify({
                    username: this.username,
                    email: this.email,
                    password: this.password
                })
            });
            const data = await response.json();
            if (response.ok) {
                window.location.href = '/auth/coming-soon/';
            } else {
                if (response.status === 400) {
                    this.errors.username = data.username ? data.username.join(' ') : null;
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