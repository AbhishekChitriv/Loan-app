document.getElementById('cibil_score').addEventListener('input', function (e) {
    document.getElementById('cibil_val').textContent = e.target.value;
});

document.getElementById('prediction-form').addEventListener('submit', async function (e) {
    e.preventDefault();

    const submitBtn = document.getElementById('submit-btn');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnLoader = submitBtn.querySelector('.btn-loader');

    // UI Loading state
    btnText.textContent = 'Processing...';
    btnLoader.classList.remove('hidden');
    submitBtn.disabled = true;

    const formData = new FormData(this);
    const data = Object.fromEntries(formData.entries());

    try {
        const response = await fetch('/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });

        const result = await response.json();

        if (result.success) {
            // Hide form and show result
            document.getElementById('prediction-form').classList.add('hidden');
            const resultCard = document.getElementById('result-card');
            resultCard.classList.remove('hidden');

            // Format as Indian Rupee
            const formattedValue = new Intl.NumberFormat('en-IN', {
                style: 'currency',
                currency: 'INR',
                maximumFractionDigits: 0
            }).format(result.prediction);

            document.getElementById('prediction-output').textContent = formattedValue;
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while fetching the prediction.');
    } finally {
        btnText.textContent = 'Check Eligibility';
        btnLoader.classList.add('hidden');
        submitBtn.disabled = false;
    }
});

function resetForm() {
    document.getElementById('prediction-form').classList.remove('hidden');
    document.getElementById('result-card').classList.add('hidden');
    document.getElementById('prediction-form').reset();
    document.getElementById('cibil_val').textContent = '650';
}
