// Smooth scroll
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Typing animation for terminal prompt
const typingText = document.querySelector('.typing-text');
if (typingText) {
    const text = typingText.textContent;
    typingText.textContent = '';
    let i = 0;

    const typeWriter = () => {
        if (i < text.length) {
            typingText.textContent += text.charAt(i);
            i++;
            setTimeout(typeWriter, 100);
        }
    };

    setTimeout(typeWriter, 500);
}

// Fade in animations on scroll
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe feature cards
document.querySelectorAll('.feature-card').forEach((el, index) => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(30px)';
    el.style.transition = `opacity 0.6s ease ${index * 0.1}s, transform 0.6s ease ${index * 0.1}s`;
    observer.observe(el);
});

// Copy code on click
document.querySelectorAll('.command-list code').forEach(code => {
    code.style.cursor = 'pointer';
    code.title = 'Click to copy';

    code.addEventListener('click', () => {
        const text = code.textContent.replace('<tool>', 'aider');
        navigator.clipboard.writeText(text).then(() => {
            const original = code.textContent;
            code.textContent = '✓ Copied';
            code.style.color = 'var(--accent)';

            setTimeout(() => {
                code.textContent = original;
                code.style.color = '';
            }, 2000);
        });
    });
});
