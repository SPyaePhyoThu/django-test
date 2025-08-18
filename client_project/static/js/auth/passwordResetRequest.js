

export default () => ({
    email: '',
    message: '',
    messageColor: '',
    isLoading: false,
    async requestReset() {
        this.isLoading = true;
        this.message = '';
        try {
            const response = await fetch('/auth/api/password-reset-request/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.$store.getCookie('csrftoken')
                },
                body: JSON.stringify({ email: this.email })
            });
            const data = await response.json();
            if (response.ok) {
                this.message = 'Password reset link sent to your email.';
                this.messageColor = 'green';
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