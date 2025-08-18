

export default () => ({
    new_password: '',
    confirm_password: '',
    uidb64: '',
    token: '',
    message: '',
    messageColor: '',
    isLoading: false,

    init() {
        const pathParts = window.location.pathname.split('/');
        if (pathParts.length >= 5) {
            this.uidb64 = pathParts[pathParts.length - 3];
            this.token = pathParts[pathParts.length - 2];
        }
    },

    async resetPassword() {
        this.isLoading = true;
        this.message = '';

        if (this.new_password !== this.confirm_password) {
            this.message = 'Passwords do not match.';
            this.messageColor = 'red';
            this.isLoading = false;
            return;
        }

        try {
            const response = await fetch('/auth/api/password-reset-confirm/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.$store.getCookie('csrftoken')
                },
                body: JSON.stringify({
                    uidb64: this.uidb64,
                    token: this.token,
                    new_password: this.new_password
                })
            });
            const data = await response.json();
            if (response.ok) {
                this.message = 'Password has been reset successfully. Redirecting to login...';
                this.messageColor = 'green';
                setTimeout(() => {
                    window.location.href = '/auth/login/';
                }, 2000);
            } else {
                this.message = 'Error: ' + (data.message || JSON.stringify(data));
                this.messageColor = 'red';
            }
        } catch (error) {
            this.message = 'An error occurred: ' + error.message;
            this.messageColor = 'red';
        } finally {
            this.isLoading = false;
        }
    }
});