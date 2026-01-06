// static/js/portfolio/portfolio-detail.js

document.addEventListener('DOMContentLoaded', () => {
    const deviceCard = document.getElementById('pfDeviceCard');

    if (deviceCard) {
        // یه تاخیر کوچیک برای حس نرم‌تر
        setTimeout(() => {
            deviceCard.classList.add('pf-device-card--in');
        }, 200);
    }
});