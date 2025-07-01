document.addEventListener('DOMContentLoaded', () => {
  // 🔐 CSRF token extractor for POST requests
  function getCSRFToken() {
    const match = document.cookie.match(/csrftoken=([\w-]+)/);
    return match ? match[1] : '';
  }

  // 1️⃣ Caption Generation
  const captionForm = document.getElementById('caption-form');
  const captionResult = document.getElementById('caption-result');

  if (captionForm && captionResult) {
    captionForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const topic = document.getElementById('caption-topic').value;
      captionResult.textContent = 'Generating...';

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
    });
  }

  // 2️⃣ Image Generation
  const imageForm = document.getElementById('image-form');
  const imageResult = document.getElementById('image-result');

  if (imageForm && imageResult) {
    imageForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const prompt = document.getElementById('image-prompt').value;
      imageResult.innerHTML = 'Generating image...';

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
    });
  }

  // 3️⃣ Engagement Prediction
  const engagementForm = document.getElementById('engagement-form');
  const engagementResult = document.getElementById('engagement-result');

  if (engagementForm && engagementResult) {
    engagementForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const caption = document.getElementById('caption-input').value;
      engagementResult.textContent = 'Analyzing...';

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
    });
  }

  // 4️⃣ Optional: Dark/Light Theme Toggle
  const toggle = document.createElement('button');
  toggle.textContent = '🌓 Toggle Theme';
  toggle.style.position = 'fixed';
  toggle.style.top = '10px';
  toggle.style.right = '10px';
  toggle.style.padding = '8px 12px';
  toggle.style.zIndex = 9999;
  toggle.style.borderRadius = '6px';
  toggle.style.backgroundColor = '#444';
  toggle.style.color = '#fff';
  toggle.style.border = 'none';
  toggle.style.cursor = 'pointer';

  document.body.appendChild(toggle);

  toggle.addEventListener('click', () => {
    document.body.classList.toggle('light-mode');
  });
});
