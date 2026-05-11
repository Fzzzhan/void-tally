// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            const offset = 80; // Navbar height
            const targetPosition = target.offsetTop - offset;
            window.scrollTo({
                top: targetPosition,
                behavior: 'smooth'
            });
        }
    });
});

// Navbar background on scroll
const navbar = document.querySelector('.navbar');
let lastScroll = 0;

window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset;

    if (currentScroll > 50) {
        navbar.style.background = 'rgba(255, 255, 255, 0.98)';
        navbar.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)';
    } else {
        navbar.style.background = 'rgba(255, 255, 255, 0.95)';
        navbar.style.boxShadow = 'none';
    }

    lastScroll = currentScroll;
});

// Add animation on scroll
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe feature cards and workflow steps
document.querySelectorAll('.feature-card, .workflow-step').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(el);
});

// Copy code snippets on click
document.querySelectorAll('.install-steps code, .setup-step code').forEach(code => {
    code.style.cursor = 'pointer';
    code.title = 'Click to copy';

    code.addEventListener('click', () => {
        const text = code.textContent;
        navigator.clipboard.writeText(text).then(() => {
            const originalText = code.textContent;
            code.textContent = '✓ Copied!';
            code.style.color = '#10b981';

            setTimeout(() => {
                code.textContent = originalText;
                code.style.color = '';
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy:', err);
        });
    });
});

// Terminal typing effect
const terminalBody = document.querySelector('.terminal-body');
if (terminalBody) {
    const originalContent = terminalBody.innerHTML;
    terminalBody.innerHTML = '';

    let delay = 0;
    const lines = originalContent.split('</div>');

    lines.forEach((line, index) => {
        if (line.trim()) {
            setTimeout(() => {
                const div = document.createElement('div');
                div.className = 'terminal-line';
                div.innerHTML = line + '</div>';
                terminalBody.appendChild(div);

                // Scroll to bottom
                terminalBody.parentElement.scrollTop = terminalBody.parentElement.scrollHeight;
            }, delay);
            delay += 300;
        }
    });
}
