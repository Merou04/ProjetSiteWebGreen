/* ============================================
   GreenSpot - JavaScript
   ============================================ */

document.addEventListener('DOMContentLoaded', function () {

    // --- Navbar scroll effect ---
    const navbar = document.getElementById('navbar');
    window.addEventListener('scroll', function () {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    // --- Mobile navigation toggle ---
    const navToggle = document.getElementById('navToggle');
    const navLinks = document.getElementById('navLinks');

    if (navToggle) {
        navToggle.addEventListener('click', function () {
            navLinks.classList.toggle('open');
            navToggle.classList.toggle('active');
        });

        // Close menu when clicking a link
        navLinks.querySelectorAll('a').forEach(function (link) {
            link.addEventListener('click', function () {
                navLinks.classList.remove('open');
                navToggle.classList.remove('active');
            });
        });
    }

    // --- Newsletter form ---
    var newsletterForm = document.getElementById('newsletterForm');
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', function (e) {
            e.preventDefault();
            var input = this.querySelector('input[type="email"]');
            if (input && input.value) {
                alert('Merci pour votre inscription ! Vous recevrez bientot nos meilleurs conseils de jardinage.');
                input.value = '';
            }
        });
    }

    // --- Scroll reveal animation ---
    var revealElements = document.querySelectorAll('.feature-card, .plant-card, .tip-card');

    function revealOnScroll() {
        revealElements.forEach(function (el) {
            var rect = el.getBoundingClientRect();
            var windowHeight = window.innerHeight;
            if (rect.top < windowHeight - 80) {
                el.classList.add('revealed');
            }
        });
    }

    // Add reveal CSS class
    revealElements.forEach(function (el) {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    });

    // Override for revealed elements
    var style = document.createElement('style');
    style.textContent = '.revealed { opacity: 1 !important; transform: translateY(0) !important; }';
    document.head.appendChild(style);

    window.addEventListener('scroll', revealOnScroll);
    revealOnScroll(); // initial check

    // --- Contact form handling ---
    var contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', function (e) {
            e.preventDefault();
            alert('Merci pour votre message ! Nous vous repondrons dans les plus brefs delais.');
            this.reset();
        });
    }

    // --- Plant filter ---
    var filterBtns = document.querySelectorAll('.filter-btn');
    var plantCards = document.querySelectorAll('.catalog-card');

    filterBtns.forEach(function (btn) {
        btn.addEventListener('click', function () {
            var filter = this.getAttribute('data-filter');

            filterBtns.forEach(function (b) { b.classList.remove('active'); });
            this.classList.add('active');

            plantCards.forEach(function (card) {
                if (filter === 'all' || card.getAttribute('data-type') === filter) {
                    card.style.display = '';
                    setTimeout(function () { card.classList.add('revealed'); }, 50);
                } else {
                    card.style.display = 'none';
                    card.classList.remove('revealed');
                }
            });
        });
    });
});
