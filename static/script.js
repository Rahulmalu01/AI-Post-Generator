document.addEventListener('DOMContentLoaded', () => {
  // 🔐 CSRF token extractor
  function getCSRFToken() {
    const match = document.cookie.match(/csrftoken=([\w-]+)/);
    return match ? match[1] : '';
  }

  // 🔄 Utility: Set loading state
  function setLoading(el, state, text = 'Generating...') {
    if (!el) return;
    if (state) {
      el.dataset.original = el.textContent;
      el.textContent = text;
      el.disabled = true;
    } else {
      el.textContent = el.dataset.original || 'Submit';
      el.disabled = false;
    }
  }

  // 1️⃣ Caption Generation
  const captionForm = document.getElementById('caption-form');
  const captionResult = document.getElementById('caption-result');
  const captionBtn = captionForm?.querySelector('button');

  captionForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const topic = document.getElementById('caption-topic').value;
    captionResult.textContent = 'Generating...';
    setLoading(captionBtn, true);

    try {
      const response = await fetch('/generate-caption/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': getCSRFToken()
        },
        body: `topic=${encodeURIComponent(topic)}`
      });

      const data = await response.json();
      captionResult.textContent = data.caption || data.error || 'Something went wrong.';
    } catch (err) {
      captionResult.textContent = 'Network error.';
    }

    setLoading(captionBtn, false);
  });

  // 2️⃣ Image Generation
  const imageForm = document.getElementById('image-form');
  const imageResult = document.getElementById('image-result');
  const imageBtn = imageForm?.querySelector('button');

  imageForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const prompt = document.getElementById('image-prompt').value;
    imageResult.innerHTML = 'Generating image...';
    setLoading(imageBtn, true);

    try {
      const response = await fetch('/generate-image/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': getCSRFToken()
        },
        body: `prompt=${encodeURIComponent(prompt)}`
      });

      const data = await response.json();
      if (data.image_url) {
        imageResult.innerHTML = `<img src="${data.image_url}" alt="Generated Image" style="max-width: 100%; margin-top: 10px;">`;
      } else {
        imageResult.textContent = data.error || 'Something went wrong.';
      }
    } catch (err) {
      imageResult.textContent = 'Network error.';
    }

    setLoading(imageBtn, false);
  });

  // 3️⃣ Engagement Prediction
  const engagementForm = document.getElementById('engagement-form');
  const engagementResult = document.getElementById('engagement-result');
  const engagementBtn = engagementForm?.querySelector('button');

  engagementForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const caption = document.getElementById('caption-input').value;
    engagementResult.textContent = 'Analyzing...';
    setLoading(engagementBtn, true);

    try {
      const response = await fetch('/predict-engagement/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': getCSRFToken()
        },
        body: `caption=${encodeURIComponent(caption)}`
      });

      const data = await response.json();
      if (data.likes && data.shares !== undefined) {
        engagementResult.innerHTML = `
          <p><strong>Predicted Likes:</strong> ${data.likes}</p>
          <p><strong>Predicted Shares:</strong> ${data.shares}</p>
        `;
      } else {
        engagementResult.textContent = data.error || 'Something went wrong.';
      }
    } catch (err) {
      engagementResult.textContent = 'Network error.';
    }

    setLoading(engagementBtn, false);
  });

  // 4️⃣ Theme Toggle with LocalStorage
  const themeToggle = document.createElement('button');
  themeToggle.textContent = '🌓 Toggle Theme';
  themeToggle.className = 'btn btn-outline';
  themeToggle.style.position = 'fixed';
  themeToggle.style.top = '10px';
  themeToggle.style.right = '10px';
  themeToggle.style.zIndex = 9999;

  document.body.appendChild(themeToggle);

  themeToggle.addEventListener('click', () => {
    document.body.classList.toggle('light-mode');
    localStorage.setItem('theme', document.body.classList.contains('light-mode') ? 'light' : 'dark');
  });

  // Load saved theme on reload
  if (localStorage.getItem('theme') === 'light') {
    document.body.classList.add('light-mode');
  }
});
