function deleteRecording(sid) {
    if (confirm('Are you sure you want to delete this recording?')) {
        fetch(`/recording/${sid}/delete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const element = document.getElementById(`recording-${sid}`);
                element.style.animation = 'fadeOut 0.5s';
                setTimeout(() => element.remove(), 500);
            } else {
                alert('Error deleting recording: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error deleting recording');
        });
    }
}

function updateFilters() {
    const days = document.getElementById('days-filter').value;
    window.location.href = `/recordings?days=${days}`;
} 