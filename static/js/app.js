/* GreenSpot — JS minimal, fonctionnel uniquement */
document.addEventListener('DOMContentLoaded', function () {

    // Navbar : effet au scroll (shadow)
    const navbar = document.getElementById('navbar');
    if (navbar) {
        window.addEventListener('scroll', function () {
            navbar.classList.toggle('scrolled', window.scrollY > 50);
        }, { passive: true }); // passive = meilleure perf scroll
    }

    // Menu mobile toggle
    const navToggle = document.getElementById('navToggle');
    const navLinks  = document.getElementById('navLinks');
    if (navToggle && navLinks) {
        navToggle.addEventListener('click', function () {
            navLinks.classList.toggle('open');
            navToggle.classList.toggle('active');
        });
        navLinks.querySelectorAll('a').forEach(function (link) {
            link.addEventListener('click', function () {
                navLinks.classList.remove('open');
                navToggle.classList.remove('active');
            });
        });
    }

    // Scroll reveal — version propre sans injection de <style>
    document.querySelectorAll('.feature-card, .spot-card').forEach(function (el) {
        el.classList.add('reveal');
    });
    function revealOnScroll() {
        document.querySelectorAll('.reveal:not(.revealed)').forEach(function (el) {
            if (el.getBoundingClientRect().top < window.innerHeight - 80) {
                el.classList.add('revealed');
            }
        });
    }
    window.addEventListener('scroll', revealOnScroll, { passive: true });
    revealOnScroll();
});