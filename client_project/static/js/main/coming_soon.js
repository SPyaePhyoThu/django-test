

export default () => ({
    isLoading: false,
    async logout() {
        this.isLoading = true;
        try {
            const response = await fetch('/auth/api/logout/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.$store.getCookie('csrftoken')
                }
            });

            if (response.ok) {
                window.location.href = '/auth/login/';
            } else {
                console.error('Logout failed');
            }
        } catch (error) {
            console.error('An error occurred:', error);
        } finally {
            this.isLoading = false;
        }
    }
});
