import loginForm from './auth/login.js';
import registerForm from './auth/register.js';
import comingSoon from './main/coming_soon.js';
import passwordResetConfirmForm from './auth/passwordResetConfirm.js';
import passwordResetRequestForm from './auth/passwordResetRequest.js';
import { getCookie } from './utils/getCookie.js';

document.addEventListener('alpine:init', () => {
    //component data
    Alpine.data('loginForm', loginForm);
    Alpine.data('registerForm', registerForm);
    Alpine.data('comingSoon', comingSoon);
    Alpine.data('passwordResetConfirmForm', passwordResetConfirmForm);
    Alpine.data('passwordResetRequestForm', passwordResetRequestForm);

    //store
    Alpine.store('getCookie', getCookie);
});
